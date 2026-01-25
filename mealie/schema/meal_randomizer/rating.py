"""Recipe rating schemas"""

from datetime import datetime
from typing import Annotated

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator


class RecipeRatingCreate(BaseModel):
    """Request to create or update a recipe rating"""

    recipe_id: Annotated[UUID4 | str, Field(description="Recipe ID to rate")]
    rating: Annotated[
        str, Field(description="Rating value: 'up' (thumbs up), 'down' (thumbs down), or 'never_again' (blacklist)")
    ]

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: str) -> str:
        """Validate rating is one of the allowed values"""
        valid_ratings = {"up", "down", "never_again"}
        normalized = v.lower().strip()
        if normalized not in valid_ratings:
            raise ValueError(f"Invalid rating: {v}. Must be one of {valid_ratings}")
        return normalized


class RecipeRatingOut(BaseModel):
    """Recipe rating response"""

    id: Annotated[UUID4, Field(description="Rating ID")]
    user_id: Annotated[UUID4, Field(description="User ID who made the rating")]
    recipe_id: Annotated[UUID4, Field(description="Recipe ID that was rated")]
    rating: Annotated[str, Field(description="Rating value ('up', 'down', or 'never_again')")]
    created_at: Annotated[datetime | None, Field(default=None, description="When the rating was created")]
    updated_at: Annotated[datetime | None, Field(default=None, description="When the rating was last updated")]

    model_config = ConfigDict(from_attributes=True)
