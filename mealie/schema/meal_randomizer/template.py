"""Randomizer template schemas"""

from datetime import datetime
from typing import Annotated, Any

from pydantic import UUID4, BaseModel, ConfigDict, Field


class RandomizerTemplateCreate(BaseModel):
    """Request to save a meal plan as a template"""

    template_name: Annotated[str, Field(min_length=1, max_length=255, description="Name for the template")]
    week_plan_json: Annotated[
        dict[str, Any] | list[dict[str, Any]],
        Field(description="Week plan data (can be dict or list of RecipeResultCard)"),
    ]


class RandomizerTemplateOut(BaseModel):
    """Full randomizer template response"""

    id: Annotated[UUID4, Field(description="Template ID")]
    user_id: Annotated[UUID4, Field(description="User ID who created the template")]
    template_name: Annotated[str, Field(description="Template name")]
    week_plan_json: Annotated[dict[str, Any], Field(description="Week plan data as JSON")]
    created_at: Annotated[datetime | None, Field(default=None, description="When the template was created")]
    updated_at: Annotated[datetime | None, Field(default=None, description="When the template was last updated")]

    model_config = ConfigDict(from_attributes=True)


class RandomizerTemplateSummary(BaseModel):
    """Summarized template for list views"""

    id: Annotated[UUID4, Field(description="Template ID")]
    template_name: Annotated[str, Field(description="Template name")]
    recipe_names: Annotated[
        list[str], Field(default_factory=list, description="List of recipe names in this template for quick preview")
    ]
    created_at: Annotated[datetime | None, Field(default=None, description="When the template was created")]

    model_config = ConfigDict(from_attributes=True)
