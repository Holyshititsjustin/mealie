"""Meal Randomizer Schemas"""

from .randomizer_request import (
    ProteinPreference,
    RandomizerFilters,
    RandomizerRequest,
)
from .randomizer_response import (
    ConsolidatedIngredient,
    RandomizerResponse,
    RecipeResultCard,
    SubstitutionSuggestion,
)
from .rating import RecipeRatingCreate, RecipeRatingOut
from .template import (
    RandomizerTemplateCreate,
    RandomizerTemplateOut,
    RandomizerTemplateSummary,
)
from .preferences import (
    RandomizerPreferencesCreate,
    RandomizerPreferencesOut,
    RandomizerPreferencesUpdate,
)

__all__ = [
    # Request schemas
    "ProteinPreference",
    "RandomizerFilters",
    "RandomizerRequest",
    # Response schemas
    "ConsolidatedIngredient",
    "RandomizerResponse",
    "RecipeResultCard",
    "SubstitutionSuggestion",
    # Rating schemas
    "RecipeRatingCreate",
    "RecipeRatingOut",
    # Template schemas
    "RandomizerTemplateCreate",
    "RandomizerTemplateOut",
    "RandomizerTemplateSummary",
    # Preferences schemas
    "RandomizerPreferencesCreate",
    "RandomizerPreferencesOut",
    "RandomizerPreferencesUpdate",
]
