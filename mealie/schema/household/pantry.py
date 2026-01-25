from __future__ import annotations

from datetime import datetime

from pydantic import UUID4, ConfigDict, field_validator
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from mealie.db.models.household.pantry import IngredientCatalogItem, PantryItem, PantryItemEvent
from mealie.db.models.recipe import IngredientFoodModel, IngredientUnitModel
from mealie.schema._mealie import MealieModel
from mealie.schema._mealie.mealie_model import UpdatedAtField
from mealie.schema.recipe.recipe_ingredient import IngredientFood, IngredientUnit
from mealie.schema.response.pagination import PaginationBase


class PantryItemBase(MealieModel):
    name: str
    notes: str | None = None
    quantity: float = 1
    unit_id: UUID4 | None = None
    food_id: UUID4 | None = None
    catalog_item_id: UUID4 | None = None
    purchased_at: datetime | None = None
    expires_at: datetime
    expiring_window_days: int | None = None
    is_archived: bool = False

    @field_validator("quantity", mode="before")
    @classmethod
    def default_quantity(cls, value):
        if value is None:
            return 1
        return value


class PantryItemCreate(PantryItemBase):
    id: UUID4 | None = None


class PantryItemUpdate(PantryItemBase):
    expired_at: datetime | None = None
    depleted_at: datetime | None = None


class IngredientCatalogItemBase(MealieModel):
    name: str
    default_shelf_life_days: int | None = None
    default_unit_id: UUID4 | None = None


class IngredientCatalogItemCreate(IngredientCatalogItemBase):
    id: UUID4 | None = None


class IngredientCatalogItemUpdate(IngredientCatalogItemBase):
    id: UUID4


class IngredientCatalogItemOut(IngredientCatalogItemUpdate):
    group_id: UUID4
    household_id: UUID4 | None = None
    default_unit: IngredientUnit | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = UpdatedAtField(None)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [joinedload(IngredientCatalogItem.default_unit)]


class PantryItemOut(PantryItemUpdate):
    id: UUID4
    group_id: UUID4
    household_id: UUID4
    unit: IngredientUnit | None = None
    food: IngredientFood | None = None
    catalog_item: IngredientCatalogItemOut | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = UpdatedAtField(None)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [
            joinedload(PantryItem.unit),
            joinedload(PantryItem.food).joinedload(IngredientFoodModel.extras),
            joinedload(PantryItem.catalog_item).joinedload(IngredientCatalogItem.default_unit),
        ]


class PantryItemPagination(PaginationBase):
    items: list[PantryItemOut]


class PantryItemEventBase(MealieModel):
    pantry_item_id: UUID4
    event_type: str
    quantity_delta: float | None = 0
    note: str | None = None
    occurred_at: datetime | None = None


class PantryItemEventCreate(PantryItemEventBase):
    id: UUID4 | None = None


class PantryItemEventOut(PantryItemEventBase):
    id: UUID4
    group_id: UUID4
    household_id: UUID4
    occurred_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = UpdatedAtField(None)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [joinedload(PantryItemEvent.pantry_item)]


class PantryItemEventPagination(PaginationBase):
    items: list[PantryItemEventOut]
