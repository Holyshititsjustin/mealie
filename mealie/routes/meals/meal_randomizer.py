from functools import cached_property

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from mealie.core.exceptions import mealie_registered_exceptions
from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.schema.meal_randomizer.randomizer_request import RandomizerRequest
from mealie.schema.meal_randomizer.randomizer_response import RandomizerResponse
from mealie.schema.meal_randomizer.rating import RecipeRatingCreate, RecipeRatingOut
from mealie.schema.meal_randomizer.template import (
    RandomizerTemplateCreate,
    RandomizerTemplateOut,
    RandomizerTemplateSummary,
)
from mealie.schema.meal_randomizer.preferences import (
    RandomizerPreferencesCreate,
    RandomizerPreferencesOut,
    RandomizerPreferencesUpdate,
)
from mealie.schema.response.responses import SuccessResponse
from mealie.services.meal_randomizer.meal_randomizer_service import MealRandomizerService

router = APIRouter(prefix="/households/meals/randomizer", tags=["Households: Meal Randomizer"])


@controller(router)
class MealRandomizerController(BaseUserController):
    """Controller for meal randomizer feature"""

    def registered_exceptions(self, ex: type[Exception]) -> str:
        registered = {
            **mealie_registered_exceptions(self.translator),
        }
        return registered.get(ex, self.t("generic.server-error"))

    @cached_property
    def randomizer_service(self) -> MealRandomizerService:
        """Lazy-load the meal randomizer service"""
        return MealRandomizerService(
            session=self.session,
            user_id=self.user.id,
            group_id=self.group_id,
        )

    @property
    def group_id(self) -> UUID4:
        """Get group_id from user's household"""
        return self.user.group_id

    # ==================== GENERATE ENDPOINT ====================

    @router.post("/generate", response_model=RandomizerResponse, status_code=200)
    def generate_week_plan(self, request: RandomizerRequest) -> RandomizerResponse:
        """
        Generate a randomized 7-day meal plan based on filters and preferences.

        Returns a complete weekly plan with:
        - 7 randomly selected recipes with dates
        - Consolidated shopping list
        - Ingredient substitution suggestions
        - Cache status and warnings if applicable
        """
        try:
            return self.randomizer_service.generate_week_plan(request)
        except ValueError as ex:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ex),
            )
        except Exception as ex:
            self.logger.exception("Error generating meal plan")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.registered_exceptions(type(ex)),
            )

    # ==================== TEMPLATE ENDPOINTS ====================

    @router.get("/templates", response_model=list[RandomizerTemplateSummary], status_code=200)
    def list_templates(self) -> list[RandomizerTemplateSummary]:
        """
        List all saved meal plan templates for the current user.

        Returns a summary of each template including:
        - Template ID and name
        - Preview of recipe names in the plan
        - Created/updated timestamps
        """
        try:
            templates = self.repos.randomizer_templates.by_user(self.user.id)
            return [
                RandomizerTemplateSummary(
                    id=t.id,
                    template_name=t.template_name,
                    recipe_names=[],  # Will be populated from week_plan_json
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in templates
            ]
        except Exception as ex:
            self.logger.exception("Error listing templates")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.registered_exceptions(type(ex)),
            )

    @router.post("/templates", response_model=RandomizerTemplateOut, status_code=201)
    def save_template(self, data: RandomizerTemplateCreate) -> RandomizerTemplateOut:
        """
        Save a generated meal plan as a reusable template.

        The template stores the complete week_plan_json for quick reuse.
        """
        try:
            template = self.repos.randomizer_templates.create(
                {
                    "user_id": self.user.id,
                    "template_name": data.template_name,
                    "week_plan_json": data.week_plan_json,
                }
            )
            return RandomizerTemplateOut.model_validate(template)
        except Exception as ex:
            self.logger.exception("Error saving template")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.registered_exceptions(type(ex)),
            )

    @router.get("/templates/{template_id}", response_model=RandomizerTemplateOut, status_code=200)
    def get_template(self, template_id: UUID4) -> RandomizerTemplateOut:
        """
        Retrieve a specific saved template by ID.
        """
        try:
            template = self.repos.randomizer_templates.get(template_id)
            if not template or template.user_id != self.user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found",
                )
            return RandomizerTemplateOut.model_validate(template)
        except HTTPException:
            raise
        except Exception as ex:
            self.logger.exception("Error retrieving template")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.registered_exceptions(type(ex)),
            )

    @router.delete("/templates/{template_id}", response_model=SuccessResponse, status_code=200)
    def delete_template(self, template_id: UUID4) -> SuccessResponse:
        """
        Delete a saved template.

        Only the template owner can delete it.
        """
        try:
            template = self.repos.randomizer_templates.get(template_id)
            if not template or template.user_id != self.user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found",
                )
            self.repos.randomizer_templates.delete(template_id)
            return SuccessResponse.respond()
        except HTTPException:
            raise
        except Exception as ex:
            self.logger.exception("Error deleting template")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.registered_exceptions(type(ex)),
            )

    # ==================== RATING ENDPOINTS ====================

    @router.post("/rate", response_model=RecipeRatingOut, status_code=201)
    def rate_recipe(self, data: RecipeRatingCreate) -> RecipeRatingOut:
        """
        Rate a recipe as thumbs up, thumbs down, or never again.

        Ratings influence future meal randomizer suggestions:
        - up: Increases likelihood of being selected
        - down: Decreases likelihood
        - never_again: Excludes from future randomization
        """
        try:
            rating = self.repos.recipe_ratings.create(
                {
                    "user_id": self.user.id,
                    "recipe_id": data.recipe_id,
                    "rating": data.rating,
                }
            )
            return RecipeRatingOut.model_validate(rating)
        except Exception as ex:
            self.logger.exception("Error rating recipe")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.registered_exceptions(type(ex)),
            )

    # ==================== PREFERENCES ENDPOINTS ====================

    @router.get("/preferences", response_model=RandomizerPreferencesOut, status_code=200)
    def get_preferences(self) -> RandomizerPreferencesOut:
        """
        Retrieve the current user's randomizer preferences.

        Returns:
        - Default filter settings
        - Recipe candidate cap (default 200)
        - Avoid repeat window in days (default 7)
        """
        try:
            prefs = self.repos.randomizer_preferences.get_by_user_id(self.user.id)
            if not prefs:
                # Return defaults if no preferences exist
                return RandomizerPreferencesOut(
                    id=None,
                    user_id=self.user.id,
                    filter_defaults={},
                    recipe_candidate_cap=200,
                    avoid_repeat_days=7,
                    created_at=None,
                    updated_at=None,
                )
            return RandomizerPreferencesOut.model_validate(prefs)
        except Exception as ex:
            self.logger.exception("Error retrieving preferences")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.registered_exceptions(type(ex)),
            )

    @router.put("/preferences", response_model=RandomizerPreferencesOut, status_code=200)
    def update_preferences(self, data: RandomizerPreferencesUpdate) -> RandomizerPreferencesOut:
        """
        Update the current user's randomizer preferences.

        Preferences can include:
        - filter_defaults: JSON object with default filter values
        - recipe_candidate_cap: Maximum recipes to consider (10-5000)
        - avoid_repeat_days: Days to avoid repeating recent recipes (1-365)
        """
        try:
            prefs = self.repos.randomizer_preferences.get_by_user_id(self.user.id)

            update_data = {}
            if data.filter_defaults is not None:
                update_data["filter_defaults"] = data.filter_defaults
            if data.recipe_candidate_cap is not None:
                update_data["recipe_candidate_cap"] = data.recipe_candidate_cap
            if data.avoid_repeat_days is not None:
                update_data["avoid_repeat_days"] = data.avoid_repeat_days

            if not prefs:
                # Create new preferences
                create_data = {
                    "user_id": self.user.id,
                    **update_data,
                }
                prefs = self.repos.randomizer_preferences.create(create_data)
            else:
                # Update existing preferences
                prefs = self.repos.randomizer_preferences.update(prefs.id, update_data)

            return RandomizerPreferencesOut.model_validate(prefs)
        except Exception as ex:
            self.logger.exception("Error updating preferences")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=self.registered_exceptions(type(ex)),
            )
