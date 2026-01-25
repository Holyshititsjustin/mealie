"""Meal Randomizer Models

Models for the meal randomizer feature, including:
- RecipeRating: User ratings for randomized recipes
- RandomizerTemplate: Saved meal plan templates
- RandomizerPreferences: User profile defaults for randomizer filters
"""

from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.guid import GUID

if TYPE_CHECKING:
    from mealie.db.models.users import User
    from mealie.db.models.recipe import RecipeModel


class RecipeRating(SqlAlchemyBase, BaseMixins):
    """User ratings for randomized recipes (thumbs up, thumbs down, never again)"""

    __tablename__ = "recipe_ratings"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "recipe_id", name="user_id_recipe_id_key"),
        sa.Index("ix_recipe_ratings_user_id", "user_id"),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id"), nullable=False, index=True)
    recipe_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("recipes.id"), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(sa.String(20), nullable=False)  # 'up', 'down', 'never_again'

    # Relationships
    user: Mapped["User"] = orm.relationship("User", foreign_keys=[user_id])
    recipe: Mapped["RecipeModel"] = orm.relationship("RecipeModel", foreign_keys=[recipe_id])


class RandomizerTemplate(SqlAlchemyBase, BaseMixins):
    """Saved meal plan templates for reuse"""

    __tablename__ = "randomizer_templates"
    __table_args__ = (sa.Index("ix_randomizer_templates_user_id", "user_id"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    user_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("users.id"), nullable=False, index=True)
    template_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    week_plan_json: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False)

    # Relationships
    user: Mapped["User"] = orm.relationship("User", foreign_keys=[user_id])


class RandomizerPreferences(SqlAlchemyBase, BaseMixins):
    """User profile defaults for randomizer filters and settings"""

    __tablename__ = "randomizer_preferences"
    __table_args__ = (sa.UniqueConstraint("user_id", name="user_id_key"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    user_id: Mapped[GUID] = mapped_column(
        GUID, sa.ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    filter_defaults: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON, nullable=True)
    recipe_candidate_cap: Mapped[int] = mapped_column(sa.Integer, default=200, nullable=False)
    avoid_repeat_days: Mapped[int] = mapped_column(sa.Integer, default=7, nullable=False)

    # Relationships
    user: Mapped["User"] = orm.relationship(
        "User", foreign_keys=[user_id], uselist=False
    )
