"""Recipe filtering service for meal randomizer

This service handles querying and filtering recipes from the database
based on randomizer criteria (dietary restrictions, allergens, cook time, etc.)
"""

import random
from datetime import datetime, timedelta
from typing import Any

from pydantic import UUID4
from sqlalchemy import and_, cast, func, or_, select, Integer
from sqlalchemy.orm import Session, joinedload

from mealie.core.root_logger import get_logger
from mealie.db.models.meal_randomizer import RecipeRating
from mealie.db.models.recipe import RecipeModel
from mealie.db.models.recipe.tag import Tag
from mealie.schema.meal_randomizer.randomizer_request import RandomizerFilters

logger = get_logger()


class RecipeFilterService:
    """Service for filtering recipes based on randomizer criteria"""

    def __init__(self, session: Session, user_id: UUID4, group_id: UUID4):
        self.session = session
        self.user_id = user_id
        self.group_id = group_id

    def get_candidate_recipes(
        self,
        filters: RandomizerFilters,
    ) -> list[RecipeModel]:
        """
        Query and filter recipes based on randomizer filters.
        
        Returns a list of Recipe models that match all criteria, ordered by:
        1. User favorites (if rated "up")
        2. Recently cooked (prioritize variety)
        3. Random shuffle
        
        Args:
            filters: RandomizerFilters with all filtering criteria
            
        Returns:
            List of RecipeModel objects matching criteria
        """
        logger.info(f"Querying candidate recipes for user {self.user_id}")
        
        # Start with base query - recipes in user's group
        query = select(RecipeModel).where(RecipeModel.group_id == self.group_id)
        
        # Apply dietary restrictions (must have all specified tags)
        if filters.dietary_restrictions:
            query = self._apply_dietary_restrictions(query, filters.dietary_restrictions)
        
        # Apply allergen exclusions (must NOT have any allergen tags)
        if filters.allergens:
            query = self._apply_allergen_exclusions(query, filters.allergens)
        
        # Apply cook time filters
        if filters.cook_time_bands:
            query = self._apply_cook_time_filters(query, filters.cook_time_bands)
        
        # Apply meal type filters
        if filters.meal_types:
            query = self._apply_meal_type_filters(query, filters.meal_types)
        
        # Apply difficulty filters
        if filters.difficulty_levels:
            query = self._apply_difficulty_filters(query, filters.difficulty_levels)
        
        # Exclude recipes cooked recently (repeat avoidance)
        query = self._exclude_recent_recipes(query, filters.avoid_repeat_days)
        
        # Exclude "never again" recipes
        query = self._exclude_never_again_recipes(query)
        
        # Eager load relationships we'll need
        query = query.options(
            joinedload(RecipeModel.recipe_ingredient),
            joinedload(RecipeModel.tags),
        )
        
        # Execute query
        recipes = list(self.session.execute(query).scalars().unique())
        
        logger.info(f"Found {len(recipes)} candidate recipes before cap")
        
        # Apply candidate cap with sampling if needed
        if filters.recipe_candidate_cap and len(recipes) > filters.recipe_candidate_cap:
            recipes = random.sample(recipes, filters.recipe_candidate_cap)
            logger.info(f"Sampled down to {filters.recipe_candidate_cap} recipes")
        
        # Sort by user preference (favorites first)
        recipes = self._sort_by_user_preference(recipes)
        
        return recipes

    def _apply_dietary_restrictions(self, query: Any, restrictions: list[str]) -> Any:
        """Filter recipes that have ALL specified dietary restriction tags"""
        # For each restriction, recipe must have a matching tag
        for restriction in restrictions:
            tag_subquery = (
                select(RecipeModel.id)
                .join(RecipeModel.tags)
                .where(
                    and_(
                        func.lower(Tag.name) == restriction.lower(),
                        RecipeModel.id == RecipeModel.id,  # Correlation
                    )
                )
            )
            query = query.where(RecipeModel.id.in_(tag_subquery))
        
        return query

    def _apply_allergen_exclusions(self, query: Any, allergens: list[str]) -> Any:
        """Exclude recipes that have ANY allergen tags"""
        # Recipe must NOT have any of these tags
        allergen_subquery = (
            select(RecipeModel.id)
            .join(RecipeModel.tags)
            .where(
                func.lower(Tag.name).in_([allergen.lower() for allergen in allergens])
            )
        )
        query = query.where(RecipeModel.id.not_in(allergen_subquery))
        
        return query

    def _apply_cook_time_filters(self, query: Any, cook_time_bands: list[str]) -> Any:
        """Filter recipes by cook time ranges"""
        conditions = []

        # total_time is stored as text; strip non-digits then cast safely to integer
        safe_total_time = cast(
            func.nullif(func.regexp_replace(RecipeModel.total_time, "[^0-9]", "", "g"), ""),
            Integer,
        )
        query = query.where(safe_total_time.isnot(None))
        
        for band in cook_time_bands:
            if band == "0-15":
                conditions.append(safe_total_time <= 15)
            elif band == "15-30":
                conditions.append(and_(safe_total_time > 15, safe_total_time <= 30))
            elif band == "30-60":
                conditions.append(and_(safe_total_time > 30, safe_total_time <= 60))
            elif band == "60+":
                conditions.append(safe_total_time > 60)
        
        if conditions:
            query = query.where(or_(*conditions))
        
        return query

    def _apply_meal_type_filters(self, query: Any, meal_types: list[str]) -> Any:
        """Filter recipes by meal type tags (quick_weeknight, slow_cooker, etc.)"""
        # Similar to dietary restrictions - check for tags
        meal_type_subquery = (
            select(RecipeModel.id)
            .join(RecipeModel.tags)
            .where(
                func.lower(Tag.name).in_([mt.lower() for mt in meal_types])
            )
        )
        query = query.where(RecipeModel.id.in_(meal_type_subquery))
        
        return query

    def _apply_difficulty_filters(self, query: Any, difficulty_levels: list[str]) -> Any:
        """Filter recipes by difficulty level"""
        # Assuming RecipeModel has a difficulty field or tag
        # For now, using tags approach
        difficulty_subquery = (
            select(RecipeModel.id)
            .join(RecipeModel.tags)
            .where(
                func.lower(Tag.name).in_([d.lower() for d in difficulty_levels])
            )
        )
        query = query.where(RecipeModel.id.in_(difficulty_subquery))
        
        return query

    def _exclude_recent_recipes(self, query: Any, avoid_repeat_days: int) -> Any:
        """Exclude recipes cooked within the last N days"""
        # This requires checking meal plan history or cooking history
        # For MVP, we'll use RecipeModel.last_made if available
        # Otherwise, skip this filter for now
        
        cutoff_date = datetime.now() - timedelta(days=avoid_repeat_days)
        
        # Assuming there's a last_made field or similar
        # If not available in RecipeModel, this will need to query meal plans
        if hasattr(RecipeModel, "last_made"):
            query = query.where(
                or_(
                    RecipeModel.last_made == None,
                    RecipeModel.last_made < cutoff_date,
                )
            )
        
        return query

    def _exclude_never_again_recipes(self, query: Any) -> Any:
        """Exclude recipes the user has rated as 'never_again'"""
        never_again_subquery = (
            select(RecipeRating.recipe_id)
            .where(
                and_(
                    RecipeRating.user_id == self.user_id,
                    RecipeRating.rating == "never_again",
                )
            )
        )
        query = query.where(RecipeModel.id.not_in(never_again_subquery))
        
        return query

    def _sort_by_user_preference(self, recipes: list[RecipeModel]) -> list[RecipeModel]:
        """
        Sort recipes by user preference:
        1. Recipes rated "up" (favorites) first
        2. Then recipes with no rating
        3. Then recipes rated "down"
        4. Random shuffle within each group
        """
        # Get user ratings
        ratings_query = select(RecipeRating).where(RecipeRating.user_id == self.user_id)
        ratings_map = {
            rating.recipe_id: rating.rating
            for rating in self.session.execute(ratings_query).scalars()
        }
        
        # Separate into groups
        favorites = []
        neutral = []
        down_voted = []
        
        for recipe in recipes:
            rating = ratings_map.get(recipe.id)
            if rating == "up":
                favorites.append(recipe)
            elif rating == "down":
                down_voted.append(recipe)
            else:
                neutral.append(recipe)
        
        # Shuffle each group
        random.shuffle(favorites)
        random.shuffle(neutral)
        random.shuffle(down_voted)
        
        # Combine: favorites > neutral > down-voted
        return favorites + neutral + down_voted

    def get_recipes_by_protein(
        self,
        candidates: list[RecipeModel],
        protein_type: str,
    ) -> list[RecipeModel]:
        """
        Filter candidate recipes by protein type.
        
        This checks recipe ingredients or tags for the specified protein.
        
        Args:
            candidates: List of pre-filtered candidate recipes
            protein_type: e.g., 'chicken', 'fish', 'beef', 'tofu', 'vegetarian'
            
        Returns:
            Recipes containing the specified protein
        """
        protein_recipes = []
        protein_lower = protein_type.lower()
        
        for recipe in candidates:
            # Check if protein appears in recipe name, description, or ingredients
            if protein_lower in recipe.name.lower():
                protein_recipes.append(recipe)
                continue
            
            if recipe.description and protein_lower in recipe.description.lower():
                protein_recipes.append(recipe)
                continue
            
            # Check ingredients
            for ingredient in recipe.recipe_ingredient:
                if ingredient.note and protein_lower in ingredient.note.lower():
                    protein_recipes.append(recipe)
                    break
                if hasattr(ingredient, "food") and ingredient.food:
                    if protein_lower in ingredient.food.name.lower():
                        protein_recipes.append(recipe)
                        break
            
            # Check tags (e.g., "chicken", "vegetarian")
            for tag in recipe.tags:
                if protein_lower in tag.name.lower():
                    protein_recipes.append(recipe)
                    break
        
        return protein_recipes

    def broaden_filters_and_retry(
        self,
        filters: RandomizerFilters,
    ) -> tuple[list[RecipeModel], str]:
        """
        Progressively broaden filters if insufficient recipes found.
        
        Returns:
            Tuple of (recipes, warning_message)
        """
        original_filters = filters.model_copy(deep=True)
        warning_parts = []
        
        # Step 1: Remove difficulty filters
        if filters.difficulty_levels:
            filters.difficulty_levels = []
            warning_parts.append("difficulty restrictions")
            recipes = self.get_candidate_recipes(filters)
            if len(recipes) >= 7:
                warning = f"Broadened filters by removing: {', '.join(warning_parts)}"
                return recipes, warning
        
        # Step 2: Remove cook time filters
        if filters.cook_time_bands:
            filters.cook_time_bands = []
            warning_parts.append("cook time restrictions")
            recipes = self.get_candidate_recipes(filters)
            if len(recipes) >= 7:
                warning = f"Broadened filters by removing: {', '.join(warning_parts)}"
                return recipes, warning
        
        # Step 3: Remove meal type filters
        if filters.meal_types:
            filters.meal_types = []
            warning_parts.append("meal type restrictions")
            recipes = self.get_candidate_recipes(filters)
            if len(recipes) >= 7:
                warning = f"Broadened filters by removing: {', '.join(warning_parts)}"
                return recipes, warning
        
        # Step 4: Reduce repeat-avoid window
        if filters.avoid_repeat_days > 3:
            filters.avoid_repeat_days = 3
            warning_parts.append("repeat-avoid window to 3 days")
            recipes = self.get_candidate_recipes(filters)
            if len(recipes) >= 7:
                warning = f"Broadened filters by reducing: {', '.join(warning_parts)}"
                return recipes, warning
        
        # If still not enough, return what we have
        recipes = self.get_candidate_recipes(filters)
        warning = f"Broadened all filters but only found {len(recipes)} recipes. Consider adding more recipes or relaxing dietary/allergen restrictions."
        
        return recipes, warning
