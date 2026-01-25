"""Randomizer preferences schemas"""

from datetime import datetime
from typing import Annotated, Any

from pydantic import UUID4, BaseModel, ConfigDict, Field


class RandomizerPreferencesCreate(BaseModel):
    """Request to create user randomizer preferences"""

    filter_defaults: Annotated[
        dict[str, Any] | None,
        Field(default=None, description="Default filter configuration (JSON serialized RandomizerFilters)"),
    ]
    recipe_candidate_cap: Annotated[
        int, Field(default=200, ge=10, le=5000, description="Default recipe candidate cap (default: 200)")
    ]
    avoid_repeat_days: Annotated[
        int, Field(default=7, ge=1, le=365, description="Default repeat-avoid window in days (default: 7)")
    ]


class RandomizerPreferencesUpdate(BaseModel):
    """Request to update user randomizer preferences (partial update)"""

    filter_defaults: Annotated[
        dict[str, Any] | None,
        Field(default=None, description="Updated default filter configuration"),
    ]
    recipe_candidate_cap: Annotated[
        int | None, Field(default=None, ge=10, le=5000, description="Updated recipe candidate cap")
    ]
    avoid_repeat_days: Annotated[int | None, Field(default=None, ge=1, le=365, description="Updated repeat-avoid window")]


class RandomizerPreferencesOut(BaseModel):
    """Randomizer preferences response"""

    id: Annotated[UUID4, Field(description="Preferences ID")]
    user_id: Annotated[UUID4, Field(description="User ID")]
    filter_defaults: Annotated[dict[str, Any] | None, Field(default=None, description="Default filter configuration")]
    recipe_candidate_cap: Annotated[int, Field(description="Recipe candidate cap")]
    avoid_repeat_days: Annotated[int, Field(description="Repeat-avoid window in days")]
    created_at: Annotated[datetime | None, Field(default=None, description="When preferences were created")]
    updated_at: Annotated[datetime | None, Field(default=None, description="When preferences were last updated")]

    model_config = ConfigDict(from_attributes=True)
