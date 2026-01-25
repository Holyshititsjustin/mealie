"""Response schemas for meal randomizer"""

from datetime import date
from typing import Annotated, Any

from pydantic import UUID4, BaseModel, ConfigDict, Field


class RecipeResultCard(BaseModel):
    """Single day's recipe in the randomized week plan"""

    day: Annotated[str, Field(description="Day of the week (e.g., 'Monday')")]
    date: Annotated[str, Field(description="ISO format date (YYYY-MM-DD)")]
    recipe_id: Annotated[UUID4 | str, Field(description="Recipe ID")]
    recipe_name: Annotated[str, Field(description="Recipe name")]
    recipe_slug: Annotated[str | None, Field(default=None, description="Recipe slug for URL")]
    cook_time_minutes: Annotated[int | None, Field(default=None, description="Cook time in minutes")]
    difficulty: Annotated[str | None, Field(default=None, description="Difficulty level")]
    dietary_tags: Annotated[list[str], Field(default_factory=list, description="Dietary tags (vegetarian, etc.)")]
    image_url: Annotated[str | None, Field(default=None, description="Recipe image URL")]
    description: Annotated[str | None, Field(default=None, description="Recipe description")]
    pinned: Annotated[bool, Field(default=False, description="Whether this day is pinned")]
    expiring_ingredients_count: Annotated[
        int, Field(default=0, description="Number of expiring pantry ingredients used in this recipe")
    ]

    model_config = ConfigDict(from_attributes=True)


class ConsolidatedIngredient(BaseModel):
    """Consolidated ingredient across multiple recipes in the week"""

    name: Annotated[str, Field(description="Ingredient name")]
    quantity: Annotated[float | None, Field(default=None, description="Total quantity needed")]
    unit: Annotated[str | None, Field(default=None, description="Unit of measurement")]
    used_in_days: Annotated[
        list[str], Field(default_factory=list, description="Days this ingredient is used (e.g., ['Monday', 'Friday'])")
    ]
    expiry_date: Annotated[str | None, Field(default=None, description="Expiry date (ISO format) if tracked")]
    note: Annotated[str | None, Field(default=None, description="Additional note about ingredient")]

    model_config = ConfigDict(from_attributes=True)


class SubstitutionSuggestion(BaseModel):
    """Ingredient substitution suggestion (cheaper/seasonal alternative)"""

    ingredient: Annotated[str, Field(description="Original ingredient name")]
    reason: Annotated[
        str,
        Field(description="Reason for substitution (e.g., 'cheaper', 'seasonal', 'higher_protein', 'lower_carb')"),
    ]
    suggested_alternative: Annotated[str, Field(description="Suggested alternative ingredient")]
    estimated_savings: Annotated[
        float | None, Field(default=None, description="Estimated cost savings (in dollars or percentage)")
    ]
    nutritional_comparison: Annotated[
        dict[str, Any] | None,
        Field(default=None, description="Optional nutritional comparison (e.g., {'protein': '+5g', 'fat': '-2g'})"),
    ]

    model_config = ConfigDict(from_attributes=True)


class RandomizerResponse(BaseModel):
    """Complete response from meal randomizer generation"""

    status: Annotated[str, Field(default="success", description="Status of the randomization")]
    week_plan: Annotated[list[RecipeResultCard], Field(description="7-day meal plan")]
    shopping_consolidated: Annotated[
        dict[str, ConsolidatedIngredient],
        Field(
            default_factory=dict,
            description="Consolidated shopping list with ingredients as keys",
        ),
    ]
    substitution_suggestions: Annotated[
        list[SubstitutionSuggestion],
        Field(default_factory=list, description="Suggested ingredient substitutions"),
    ]
    metadata: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="Additional metadata (e.g., generated_at, filters_applied, recipes_searched)",
        ),
    ]
    cached: Annotated[bool, Field(default=False, description="Whether this result was served from cache")]
    warning: Annotated[
        str | None,
        Field(
            default=None,
            description="Warning message (e.g., 'Insufficient recipes found; filters were broadened automatically')",
        ),
    ]

    model_config = ConfigDict(from_attributes=True)
