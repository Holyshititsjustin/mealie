from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import UUID4

from mealie.repos.all_repositories import AllRepositories
from mealie.schema.household.household_preferences import ReadHouseholdPreferences
from mealie.schema.household.pantry import (
    IngredientCatalogItemCreate,
    IngredientCatalogItemOut,
    IngredientCatalogItemUpdate,
    PantryItemCreate,
    PantryItemEventCreate,
    PantryItemEventOut,
    PantryItemOut,
    PantryItemUpdate,
)
from mealie.schema.response.pagination import OrderDirection, PaginationQuery

WINDOW_MAX_DAYS = 30


def _clamp_window(value: int | None, default: int) -> int:
    if value is None:
        return default
    return max(0, min(WINDOW_MAX_DAYS, value))


class PantryService:
    def __init__(self, repos: AllRepositories) -> None:
        self.repos = repos
        self.items = repos.pantry_items
        self.events = repos.pantry_item_events
        self.catalog = repos.ingredient_catalog_items
        self.preferences = repos.household_preferences

    # ------------------------------------------------------------------
    # Preferences

    def _get_preferences(self) -> ReadHouseholdPreferences | None:
        if not self.repos.household_id:
            return None
        return self.preferences.get_one(self.repos.household_id, key="household_id")

    # ------------------------------------------------------------------
    # Catalog

    def upsert_catalog_item(
        self, payload: IngredientCatalogItemCreate | IngredientCatalogItemUpdate
    ) -> IngredientCatalogItemOut:
        if isinstance(payload, IngredientCatalogItemUpdate):
            return self.catalog.update(payload.id, payload)

        return self.catalog.create(payload)

    # ------------------------------------------------------------------
    # Items

    @staticmethod
    def _to_update_payload(item: PantryItemOut) -> PantryItemUpdate:
        data = item.model_dump(
            exclude={
                "id",
                "group_id",
                "household_id",
                "unit",
                "food",
                "catalog_item",
                "created_at",
                "updated_at",
            }
        )
        return PantryItemUpdate(**data)

    def create_item(self, data: PantryItemCreate) -> PantryItemOut:
        if data.expiring_window_days:
            data.expiring_window_days = _clamp_window(data.expiring_window_days, 3)

        if data.purchased_at is None:
            data.purchased_at = datetime.now(tz=UTC)

        created = self.items.create(data)
        self._record_event(created.id, "created", quantity_delta=created.quantity)
        return created

    def update_item(self, item_id: UUID4, data: PantryItemUpdate) -> PantryItemOut:
        if data.expiring_window_days:
            data.expiring_window_days = _clamp_window(data.expiring_window_days, 3)

        updated = self.items.update(item_id, data)
        return updated

    def delete_item(self, item_id: UUID4) -> PantryItemOut | None:
        deleted = self.items.delete_one(item_id)
        if deleted:
            self._record_event(item_id, "deleted")
        return deleted

    def decrement_quantity(self, item_id: UUID4, amount: float) -> PantryItemOut:
        item = self.items.get_one(item_id)
        new_qty = max(0, (item.quantity or 0) - amount)

        update_payload = self._to_update_payload(item)
        update_payload.quantity = new_qty
        if new_qty <= 0:
            update_payload.depleted_at = datetime.now(tz=UTC)

        updated = self.items.update(item_id, update_payload)
        self._record_event(item_id, "decrement", quantity_delta=-abs(amount))

        if new_qty <= 0:
            self._record_event(item_id, "depleted", quantity_delta=0)

        return updated

    def mark_consumed(self, item_id: UUID4) -> PantryItemOut:
        item = self.items.get_one(item_id)
        update_payload = self._to_update_payload(item)
        update_payload.quantity = 0
        update_payload.depleted_at = datetime.now(tz=UTC)
        updated = self.items.update(item_id, update_payload)
        self._record_event(item_id, "consumed", quantity_delta=-(item.quantity or 0))
        return updated

    def mark_discarded(self, item_id: UUID4) -> PantryItemOut:
        item = self.items.get_one(item_id)
        update_payload = self._to_update_payload(item)
        update_payload.is_archived = True
        update_payload.depleted_at = datetime.now(tz=UTC)
        updated = self.items.update(item_id, update_payload)
        self._record_event(item_id, "discarded", quantity_delta=-(item.quantity or 0))
        return updated

    # ------------------------------------------------------------------
    # Queries

    def get_expiring_items(self, override_window_days: int | None = None) -> list[PantryItemOut]:
        prefs = self._get_preferences()
        window_days = _clamp_window(override_window_days, prefs.pantry_expiring_soon_window_days if prefs else 3)
        now = datetime.now(tz=UTC)
        cutoff = now + timedelta(days=window_days)
        items = self.items.page_all(
            PaginationQuery(per_page=-1, order_by="expires_at", order_direction=OrderDirection.asc)
        ).items
        expiring: list[PantryItemOut] = []
        for item in items:
            if item.is_archived:
                continue
            if item.expires_at and now <= item.expires_at <= cutoff:
                if item.expired_at is None and item.expires_at < now:
                    self._mark_expired(item)
                expiring.append(item)
        return expiring

    def get_recently_expired_items(self, override_window_days: int | None = None) -> list[PantryItemOut]:
        prefs = self._get_preferences()
        window_days = _clamp_window(override_window_days, prefs.pantry_expired_window_days if prefs else 7)
        now = datetime.now(tz=UTC)
        lower = now - timedelta(days=window_days)
        items = self.items.page_all(
            PaginationQuery(per_page=-1, order_by="expires_at", order_direction=OrderDirection.desc)
        ).items
        expired: list[PantryItemOut] = []
        for item in items:
            if item.is_archived:
                continue
            if item.expires_at and item.expires_at < now and item.expires_at >= lower:
                expired.append(self._mark_expired(item))
        return expired

    # ------------------------------------------------------------------
    # Events

    def _record_event(
        self, pantry_item_id: UUID4, event_type: str, quantity_delta: float | None = None, note: str | None = None
    ) -> PantryItemEventOut:
        payload = PantryItemEventCreate(
            pantry_item_id=pantry_item_id,
            event_type=event_type,
            quantity_delta=quantity_delta,
            note=note,
            occurred_at=datetime.now(tz=UTC),
        )
        return self.events.create(payload)

    def _mark_expired(self, item: PantryItemOut) -> PantryItemOut:
        if item.expired_at:
            return item

        update_payload = self._to_update_payload(item)
        update_payload.expired_at = datetime.now(tz=UTC)
        updated = self.items.update(item.id, update_payload)
        self._record_event(item.id, "expired")
        return updated
