"""Request schemas for meal randomizer"""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class ProteinPreference(BaseModel):
    """User's protein distribution preference for the week"""

    protein_type: Annotated[
        str,
        Field(
            description="Type of protein (e.g., 'chicken', 'fish', 'beef', 'pork', 'tofu', 'lentils', 'vegetarian')"
        ),
    ]
    count: Annotated[int, Field(ge=0, le=7, description="Number of times this protein should appear in the week")]

    @field_validator("protein_type")
    @classmethod
    def validate_protein_type(cls, v: str) -> str:
        """Normalize protein type to lowercase"""
        return v.lower().strip()


class RandomizerFilters(BaseModel):
    """All filter parameters for meal randomization"""

    dietary_restrictions: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="List of dietary restrictions (e.g., 'vegetarian', 'vegan', 'gluten_free', 'keto', 'paleo')",
        ),
    ]
    allergens: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="List of allergens to avoid (e.g., 'nuts', 'dairy', 'shellfish', 'soy', 'eggs')",
        ),
    ]
    protein_preferences: Annotated[
        list[ProteinPreference],
        Field(
            default_factory=list,
            description="Protein distribution for the week (e.g., [{'protein_type': 'chicken', 'count': 3}])",
        ),
    ]
    avoid_repeat_days: Annotated[
        int,
        Field(
            default=7, ge=1, le=365, description="Avoid repeating recipes within this many days (default: 7 days)"
        ),
    ]
    cook_time_bands: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="Cooking time ranges (e.g., ['0-15', '15-30', '30-60', '60+'])",
        ),
    ]
    meal_types: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="Meal types (e.g., 'quick_weeknight', 'slow_cooker', 'one_pot', 'fancy')",
        ),
    ]
    difficulty_levels: Annotated[
        list[str],
        Field(default_factory=list, description="Difficulty levels (e.g., 'easy', 'medium', 'complex')"),
    ]
    include_expiring_ingredients: Annotated[
        bool,
        Field(default=False, description="Prioritize recipes using ingredients marked to expire soon"),
    ]
    recipe_candidate_cap: Annotated[
        int | None,
        Field(
            default=200,
            ge=10,
            le=5000,
            description="Maximum number of candidate recipes to consider (default: 200; user-adjustable)",
        ),
    ]

    @field_validator("cook_time_bands")
    @classmethod
    def validate_cook_time_bands(cls, v: list[str]) -> list[str]:
        """Validate cook time band format"""
        valid_bands = {"0-15", "15-30", "30-60", "60+"}
        for band in v:
            if band not in valid_bands:
                raise ValueError(f"Invalid cook time band: {band}. Must be one of {valid_bands}")
        return v

    @field_validator("meal_types")
    @classmethod
    def validate_meal_types(cls, v: list[str]) -> list[str]:
        """Normalize meal types to lowercase"""
        return [meal_type.lower().strip().replace(" ", "_") for meal_type in v]

    @field_validator("difficulty_levels")
    @classmethod
    def validate_difficulty_levels(cls, v: list[str]) -> list[str]:
        """Validate difficulty levels"""
        valid_levels = {"easy", "medium", "complex", "hard"}
        normalized = [level.lower().strip() for level in v]
        for level in normalized:
            if level not in valid_levels:
                raise ValueError(f"Invalid difficulty level: {level}. Must be one of {valid_levels}")
        return normalized


class RandomizerRequest(BaseModel):
    """Request to generate a randomized meal plan"""

    start_date: Annotated[
        date | str,
        Field(description="Starting date for the week plan (ISO format: YYYY-MM-DD or date object)"),
    ]
    filters: Annotated[RandomizerFilters, Field(description="Filtering criteria for randomization")]
    pinned_days: Annotated[
        dict[str, str],
        Field(
            default_factory=dict,
            description="Pinned recipes by day name (e.g., {'Monday': 'recipe-id-123', 'Wednesday': 'recipe-id-456'})",
        ),
    ]

    @field_validator("start_date", mode="before")
    @classmethod
    def validate_start_date(cls, v) -> str:
        """Ensure start_date is in ISO format string"""
        if isinstance(v, date):
            return v.isoformat()
        return v

    @field_validator("pinned_days")
    @classmethod
    def validate_pinned_days(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate pinned days have valid day names"""
        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        for day in v.keys():
            if day not in valid_days:
                raise ValueError(f"Invalid day name: {day}. Must be one of {valid_days}")
        return v
