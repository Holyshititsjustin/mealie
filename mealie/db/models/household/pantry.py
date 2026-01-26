from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID
from mealie.db.models.recipe.ingredient import IngredientFoodModel, IngredientUnitModel

if TYPE_CHECKING:
    from mealie.db.models.group import Group
    from mealie.db.models.household import Household


class IngredientCatalogItem(SqlAlchemyBase, BaseMixins):
    __tablename__ = "ingredient_catalog_items"
    __table_args__ = (sa.UniqueConstraint("group_id", "name", name="ingredient_catalog_group_name_key"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id"), nullable=False, index=True)
    household_id: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("households.id"), index=True)

    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    default_shelf_life_days: Mapped[int | None] = mapped_column(sa.Integer)

    default_unit_id: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("ingredient_units.id"), index=True)
    default_unit: Mapped[IngredientUnitModel | None] = relationship(IngredientUnitModel, uselist=False)

    pantry_items: Mapped[list["PantryItem"]] = relationship("PantryItem", back_populates="catalog_item")

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class PantryItem(SqlAlchemyBase, BaseMixins):
    __tablename__ = "pantry_items"
    __table_args__ = (
        sa.CheckConstraint("expiring_window_days <= 30", name="pantry_item_expiring_window_days_max_30"),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id"), nullable=False, index=True)
    household_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("households.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(sa.String, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(sa.String)

    quantity: Mapped[float] = mapped_column(sa.Float, default=1)
    unit_id: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("ingredient_units.id"), index=True)
    unit: Mapped[IngredientUnitModel | None] = relationship(IngredientUnitModel, uselist=False)

    food_id: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("ingredient_foods.id"), index=True)
    food: Mapped[IngredientFoodModel | None] = relationship(IngredientFoodModel, uselist=False)

    catalog_item_id: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("ingredient_catalog_items.id"), index=True)
    catalog_item: Mapped[Optional[IngredientCatalogItem]] = relationship(
        IngredientCatalogItem, back_populates="pantry_items"
    )

    purchased_at: Mapped[datetime] = mapped_column(sa.DateTime(), nullable=False, server_default=sa.func.now())
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(), nullable=False, index=True)
    expiring_window_days: Mapped[int | None] = mapped_column(sa.Integer)

    expired_at: Mapped[datetime | None] = mapped_column(sa.DateTime())
    depleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime())
    is_archived: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    events: Mapped[list["PantryItemEvent"]] = relationship(
        "PantryItemEvent", back_populates="pantry_item", cascade="all, delete-orphan"
    )

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class PantryItemEvent(SqlAlchemyBase, BaseMixins):
    __tablename__ = "pantry_item_events"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    pantry_item_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("pantry_items.id"), index=True, nullable=False)
    pantry_item: Mapped[PantryItem] = relationship("PantryItem", back_populates="events")

    group_id: AssociationProxy[GUID] = association_proxy("pantry_item", "group_id")
    household_id: AssociationProxy[GUID] = association_proxy("pantry_item", "household_id")

    event_type: Mapped[str] = mapped_column(sa.String, nullable=False, index=True)
    quantity_delta: Mapped[float | None] = mapped_column(sa.Float, default=0)
    note: Mapped[str | None] = mapped_column(sa.String)
    occurred_at: Mapped[datetime] = mapped_column(sa.DateTime(), nullable=False, server_default=sa.func.now())

    @auto_init()
    def __init__(self, **_) -> None:
        pass
