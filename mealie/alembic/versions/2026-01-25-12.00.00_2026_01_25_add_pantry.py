"""Add pantry and ingredient catalog tables

Revision ID: 2026_01_25_add_pantry
Revises: 2026_01_24_meal_randomizer
Create Date: 2026-01-25 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "2026_01_25_add_pantry"
down_revision: str | None = "2026_01_24_meal_randomizer"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    # ingredient catalog
    op.create_table(
        "ingredient_catalog_items",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("group_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("household_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("default_shelf_life_days", sa.Integer(), nullable=True),
        sa.Column("default_unit_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("update_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name="fk_ingredient_catalog_items_group_id"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], name="fk_ingredient_catalog_items_household_id"),
        sa.ForeignKeyConstraint(["default_unit_id"], ["ingredient_units.id"], name="fk_ingredient_catalog_items_unit_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "name", name="ingredient_catalog_group_name_key"),
    )
    op.create_index(
        "ix_ingredient_catalog_items_group_id",
        "ingredient_catalog_items",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_ingredient_catalog_items_household_id",
        "ingredient_catalog_items",
        ["household_id"],
        unique=False,
    )
    op.create_index(
        "ix_ingredient_catalog_items_default_unit_id",
        "ingredient_catalog_items",
        ["default_unit_id"],
        unique=False,
    )

    # pantry items
    op.create_table(
        "pantry_items",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("group_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("household_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("food_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("catalog_item_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("purchased_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("expiring_window_days", sa.Integer(), nullable=True),
        sa.Column("expired_at", sa.DateTime(), nullable=True),
        sa.Column("depleted_at", sa.DateTime(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("update_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("expiring_window_days <= 30", name="pantry_item_expiring_window_days_max_30"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name="fk_pantry_items_group_id"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], name="fk_pantry_items_household_id"),
        sa.ForeignKeyConstraint(["unit_id"], ["ingredient_units.id"], name="fk_pantry_items_unit_id"),
        sa.ForeignKeyConstraint(["food_id"], ["ingredient_foods.id"], name="fk_pantry_items_food_id"),
        sa.ForeignKeyConstraint(["catalog_item_id"], ["ingredient_catalog_items.id"], name="fk_pantry_items_catalog_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pantry_items_group_id", "pantry_items", ["group_id"], unique=False)
    op.create_index("ix_pantry_items_household_id", "pantry_items", ["household_id"], unique=False)
    op.create_index("ix_pantry_items_expires_at", "pantry_items", ["expires_at"], unique=False)
    op.create_index("ix_pantry_items_catalog_item_id", "pantry_items", ["catalog_item_id"], unique=False)
    op.create_index("ix_pantry_items_unit_id", "pantry_items", ["unit_id"], unique=False)
    op.create_index("ix_pantry_items_food_id", "pantry_items", ["food_id"], unique=False)
    op.create_index("ix_pantry_items_is_archived", "pantry_items", ["is_archived"], unique=False)

    # pantry events
    op.create_table(
        "pantry_item_events",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("pantry_item_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("quantity_delta", sa.Float(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("update_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["pantry_item_id"], ["pantry_items.id"], name="fk_pantry_item_events_item_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pantry_item_events_item_id", "pantry_item_events", ["pantry_item_id"], unique=False)
    op.create_index("ix_pantry_item_events_event_type", "pantry_item_events", ["event_type"], unique=False)
    op.create_index("ix_pantry_item_events_occurred_at", "pantry_item_events", ["occurred_at"], unique=False)

    # household preferences additions
    op.add_column(
        "household_preferences",
        sa.Column("pantry_expiring_soon_window_days", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "household_preferences",
        sa.Column("pantry_expired_window_days", sa.Integer(), nullable=False, server_default="7"),
    )
    op.add_column(
        "household_preferences",
        sa.Column("pantry_notifications_in_app", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "household_preferences",
        sa.Column("pantry_notifications_email", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "household_preferences",
        sa.Column("pantry_notifications_push", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "household_preferences",
        sa.Column("pantry_digest_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "household_preferences",
        sa.Column("pantry_digest_hour_utc", sa.Integer(), nullable=False, server_default="12"),
    )
    op.create_check_constraint(
        "household_preferences_expiring_window_max_30",
        "household_preferences",
        "pantry_expiring_soon_window_days <= 30 AND pantry_expired_window_days <= 30",
    )


def downgrade():
    op.drop_constraint("household_preferences_expiring_window_max_30", "household_preferences", type_="check")
    op.drop_column("household_preferences", "pantry_digest_hour_utc")
    op.drop_column("household_preferences", "pantry_digest_enabled")
    op.drop_column("household_preferences", "pantry_notifications_push")
    op.drop_column("household_preferences", "pantry_notifications_email")
    op.drop_column("household_preferences", "pantry_notifications_in_app")
    op.drop_column("household_preferences", "pantry_expired_window_days")
    op.drop_column("household_preferences", "pantry_expiring_soon_window_days")

    op.drop_index("ix_pantry_item_events_occurred_at", table_name="pantry_item_events")
    op.drop_index("ix_pantry_item_events_event_type", table_name="pantry_item_events")
    op.drop_index("ix_pantry_item_events_item_id", table_name="pantry_item_events")
    op.drop_table("pantry_item_events")

    op.drop_index("ix_pantry_items_is_archived", table_name="pantry_items")
    op.drop_index("ix_pantry_items_food_id", table_name="pantry_items")
    op.drop_index("ix_pantry_items_unit_id", table_name="pantry_items")
    op.drop_index("ix_pantry_items_catalog_item_id", table_name="pantry_items")
    op.drop_index("ix_pantry_items_expires_at", table_name="pantry_items")
    op.drop_index("ix_pantry_items_household_id", table_name="pantry_items")
    op.drop_index("ix_pantry_items_group_id", table_name="pantry_items")
    op.drop_table("pantry_items")

    op.drop_index("ix_ingredient_catalog_items_default_unit_id", table_name="ingredient_catalog_items")
    op.drop_index("ix_ingredient_catalog_items_household_id", table_name="ingredient_catalog_items")
    op.drop_index("ix_ingredient_catalog_items_group_id", table_name="ingredient_catalog_items")
    op.drop_table("ingredient_catalog_items")
