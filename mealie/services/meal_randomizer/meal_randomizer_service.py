"""Main meal randomizer service

This service orchestrates the entire randomization process:
- Protein distribution across the week
- Balance and variety rules
- Shopping list consolidation
- Result caching
"""

import random
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from pydantic import UUID4
from sqlalchemy.orm import Session

from mealie.core.root_logger import get_logger
from mealie.db.models.recipe import RecipeModel
from mealie.schema.meal_randomizer.randomizer_request import (
    ProteinPreference,
    RandomizerFilters,
    RandomizerRequest,
)
from mealie.schema.meal_randomizer.randomizer_response import (
    ConsolidatedIngredient,
    RandomizerResponse,
    RecipeResultCard,
    SubstitutionSuggestion,
)
from mealie.services.meal_randomizer.recipe_filter_service import RecipeFilterService

logger = get_logger()


class NotEnoughRecipesError(Exception):
    """Raised when insufficient recipes match the criteria"""

    pass


class MealRandomizerService:
    """Main service for generating randomized meal plans"""

    def __init__(self, session: Session, user_id: UUID4, group_id: UUID4):
        self.session = session
        self.user_id = user_id
        self.group_id = group_id
        self.filter_service = RecipeFilterService(session, user_id, group_id)
        self._cache: dict[str, tuple[RandomizerResponse, datetime]] = {}

    def generate_week_plan(
        self,
        request: RandomizerRequest,
    ) -> RandomizerResponse:
        """
        Generate a randomized 7-day meal plan.
        
        Main algorithm:
        1. Get candidate recipes (filtered, capped, ordered)
        2. Handle pinned days
        3. Distribute proteins across unassigned days
        4. Apply balance rules (avoid clustering)
        5. Consolidate shopping list
        6. Generate substitution suggestions
        7. Cache result
        
        Args:
            request: RandomizerRequest with filters and pinned days
            
        Returns:
            RandomizerResponse with week plan, shopping list, and metadata
        """
        logger.info(f"Generating week plan for user {self.user_id}")
        
        # Check cache first
        cache_key = self._generate_cache_key(request)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info("Returning cached result")
            cached_result.cached = True
            return cached_result
        
        # Step 1: Get candidate recipes
        candidates = self.filter_service.get_candidate_recipes(request.filters)
        
        warning = None
        if len(candidates) < 7:
            logger.warning(f"Insufficient recipes ({len(candidates)}). Broadening filters...")
            candidates, warning = self.filter_service.broaden_filters_and_retry(request.filters)
            
            if len(candidates) < 7:
                raise NotEnoughRecipesError(
                    f"Only {len(candidates)} recipes match your criteria. "
                    "Please add more recipes or relax your filters (dietary restrictions, allergens, etc.)."
                )
        
        # Step 2: Initialize week plan with pinned days
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        week_plan: dict[str, RecipeModel] = {}
        pinned_recipes: dict[str, RecipeModel] = {}
        
        # Load pinned recipes
        for day, recipe_id in request.pinned_days.items():
            recipe = self.session.get(RecipeModel, recipe_id)
            if recipe:
                pinned_recipes[day] = recipe
                week_plan[day] = recipe
        
        unassigned_days = [d for d in days if d not in pinned_recipes]
        
        # Step 3: Distribute proteins across unassigned days
        protein_queue = self._create_protein_queue(request.filters.protein_preferences, len(unassigned_days))
        
        for day in unassigned_days:
            protein_needed = protein_queue.pop(0) if protein_queue else None
            
            # Select recipe matching protein preference
            recipe = self._select_recipe_for_protein(
                candidates,
                protein_needed,
                existing_week_plan=week_plan,
            )
            
            if not recipe:
                # Fallback: pick any unused recipe
                recipe = self._select_any_unused_recipe(candidates, week_plan)
            
            if not recipe:
                raise NotEnoughRecipesError(
                    f"Ran out of candidate recipes while generating week plan. "
                    "Please add more recipes or broaden your filters."
                )
            
            week_plan[day] = recipe
        
        # Step 4: Apply balance rules (avoid clustering similar recipes)
        week_plan = self._apply_balance_rules(week_plan, candidates)
        
        # Step 5: Convert to response format
        start_date = datetime.fromisoformat(str(request.start_date))
        recipe_cards = []
        
        for i, day in enumerate(days):
            recipe = week_plan[day]
            card = RecipeResultCard(
                day=day,
                date=(start_date + timedelta(days=i)).isoformat(),
                recipe_id=str(recipe.id),
                recipe_name=recipe.name,
                recipe_slug=recipe.slug if hasattr(recipe, "slug") else None,
                cook_time_minutes=self._parse_cook_time(recipe.total_time if hasattr(recipe, "total_time") else None),
                difficulty=self._extract_difficulty(recipe),
                dietary_tags=[tag.name for tag in recipe.tags] if recipe.tags else [],
                image_url=recipe.image if hasattr(recipe, "image") else None,
                description=recipe.description if hasattr(recipe, "description") else None,
                pinned=day in pinned_recipes,
            )
            recipe_cards.append(card)
        
        # Step 6: Consolidate shopping list
        shopping_list = self._consolidate_shopping_list([r for r in week_plan.values()])
        
        # Step 7: Generate substitution suggestions
        substitutions = self._generate_substitution_suggestions(shopping_list)
        
        # Step 8: Build response
        response = RandomizerResponse(
            status="success",
            week_plan=recipe_cards,
            shopping_consolidated=shopping_list,
            substitution_suggestions=substitutions,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "filters_applied": request.filters.model_dump(),
                "recipes_searched": len(candidates),
                "user_id": str(self.user_id),
            },
            cached=False,
            warning=warning,
        )
        
        # Step 9: Cache result
        self._cache_result(cache_key, response)
        
        logger.info(f"Successfully generated week plan with {len(recipe_cards)} days")
        return response

    def _parse_cook_time(self, value: Any) -> int | None:
        """Best-effort parse of cook time values stored as text.

        Handles values like "45", "45 minutes", "1 hour", "1 hr 30 min".
        Returns minutes as int or None if unparsable.
        """
        if value is None:
            return None

        text = str(value).strip().lower()

        # Quick pure-integer path
        if text.isdigit():
            return int(text)

        # Find all numbers in the string
        numbers = [int(n) for n in re.findall(r"\d+", text)]
        if not numbers:
            return None

        # If mentions hours, convert first number to minutes
        if "hour" in text or "hr" in text:
            minutes = numbers[0] * 60
            # If a second number exists (e.g., "1 hr 30 min"), add it
            if len(numbers) > 1:
                minutes += numbers[1]
            return minutes

        # Otherwise use the first number as minutes
        return numbers[0]

    def _create_protein_queue(
        self,
        protein_preferences: list[ProteinPreference],
        total_days: int,
    ) -> list[str]:
        """
        Create a queue of protein types based on user preferences.
        
        Example: [ProteinPreference(protein_type="chicken", count=3)] 
        -> ["chicken", "chicken", "chicken"]
        """
        queue = []
        
        for pref in protein_preferences:
            queue.extend([pref.protein_type] * pref.count)
        
        # If queue is shorter than total days, fill remainder with None (any protein)
        while len(queue) < total_days:
            queue.append(None)
        
        # If queue is longer, truncate
        queue = queue[:total_days]
        
        # Shuffle to randomize protein distribution across week
        random.shuffle(queue)
        
        return queue

    def _select_recipe_for_protein(
        self,
        candidates: list[RecipeModel],
        protein_type: str | None,
        existing_week_plan: dict[str, RecipeModel],
    ) -> RecipeModel | None:
        """
        Select a recipe matching the protein type that hasn't been used yet.
        """
        used_recipe_ids = {recipe.id for recipe in existing_week_plan.values()}
        
        if protein_type:
            # Filter candidates by protein type
            protein_matches = self.filter_service.get_recipes_by_protein(candidates, protein_type)
            available = [r for r in protein_matches if r.id not in used_recipe_ids]
        else:
            available = [r for r in candidates if r.id not in used_recipe_ids]
        
        if available:
            return random.choice(available)
        
        return None

    def _select_any_unused_recipe(
        self,
        candidates: list[RecipeModel],
        existing_week_plan: dict[str, RecipeModel],
    ) -> RecipeModel | None:
        """Fallback: select any recipe that hasn't been used in the week"""
        used_recipe_ids = {recipe.id for recipe in existing_week_plan.values()}
        available = [r for r in candidates if r.id not in used_recipe_ids]
        
        if available:
            return random.choice(available)
        
        return None

    def _apply_balance_rules(
        self,
        week_plan: dict[str, RecipeModel],
        candidates: list[RecipeModel],
    ) -> dict[str, RecipeModel]:
        """
        Apply balance rules to avoid clustering similar recipe types.
        
        For example, avoid 3+ pasta dishes in one week.
        """
        # Check for recipe category clustering (e.g., "pasta", "salad", "soup")
        category_counts: dict[str, list[str]] = defaultdict(list)
        
        for day, recipe in week_plan.items():
            # Extract category from recipe name or tags
            categories = self._extract_categories(recipe)
            for category in categories:
                category_counts[category].append(day)
        
        # If any category appears 3+ times, try to swap one out
        for category, days_list in category_counts.items():
            if len(days_list) >= 3:
                logger.info(f"Found {len(days_list)} {category} dishes. Attempting to rebalance...")
                
                # Try to swap one of the middle occurrences
                day_to_swap = days_list[1]  # Swap the second occurrence
                
                # Find a replacement from a different category
                used_ids = {recipe.id for recipe in week_plan.values()}
                replacement = None
                
                for candidate in candidates:
                    if candidate.id in used_ids:
                        continue
                    
                    cand_categories = self._extract_categories(candidate)
                    if category not in cand_categories:
                        replacement = candidate
                        break
                
                if replacement:
                    logger.info(f"Swapping {week_plan[day_to_swap].name} with {replacement.name}")
                    week_plan[day_to_swap] = replacement
        
        return week_plan

    def _extract_categories(self, recipe: RecipeModel) -> list[str]:
        """Extract recipe categories from name and tags"""
        categories = []
        
        recipe_name_lower = recipe.name.lower()
        category_keywords = {
            "pasta": ["pasta", "spaghetti", "penne", "lasagna", "macaroni"],
            "salad": ["salad", "greens"],
            "soup": ["soup", "stew", "chili"],
            "pizza": ["pizza"],
            "sandwich": ["sandwich", "burger", "wrap"],
            "rice": ["rice", "risotto", "pilaf"],
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in recipe_name_lower for kw in keywords):
                categories.append(category)
        
        # Also check tags
        if recipe.tags:
            for tag in recipe.tags:
                tag_name_lower = tag.name.lower()
                for category, keywords in category_keywords.items():
                    if any(kw in tag_name_lower for kw in keywords):
                        if category not in categories:
                            categories.append(category)
        
        return categories

    def _extract_difficulty(self, recipe: RecipeModel) -> str | None:
        """Extract difficulty from recipe tags"""
        if not recipe.tags:
            return None
        
        for tag in recipe.tags:
            tag_lower = tag.name.lower()
            if tag_lower in ["easy", "medium", "complex", "hard"]:
                return tag_lower.capitalize()
        
        return None

    def _consolidate_shopping_list(
        self,
        recipes: list[RecipeModel],
    ) -> dict[str, ConsolidatedIngredient]:
        """
        Consolidate ingredients across all recipes in the week.
        
        Returns a dict mapping ingredient name -> ConsolidatedIngredient
        """
        ingredient_map: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"quantity": 0.0, "unit": None, "used_in_days": [], "name": ""}
        )
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        recipe_to_day = {recipe.id: day_names[i] for i, recipe in enumerate(recipes)}
        
        for recipe in recipes:
            day = recipe_to_day.get(recipe.id, "Unknown")
            
            for ingredient in recipe.recipe_ingredient:
                # Extract ingredient name
                name = ingredient.note or "Unknown Ingredient"
                if hasattr(ingredient, "food") and ingredient.food:
                    name = ingredient.food.name
                
                # Normalize name for grouping
                name_key = name.lower().strip()
                
                # Add/update in map
                if not ingredient_map[name_key]["name"]:
                    ingredient_map[name_key]["name"] = name
                
                # Add quantity (if parseable)
                if hasattr(ingredient, "quantity") and ingredient.quantity:
                    try:
                        ingredient_map[name_key]["quantity"] += float(ingredient.quantity)
                    except (ValueError, TypeError):
                        pass
                
                # Store unit (first encountered) as string
                if not ingredient_map[name_key]["unit"] and hasattr(ingredient, "unit"):
                    unit_obj = ingredient.unit
                    unit_str = None
                    if hasattr(unit_obj, "name"):
                        unit_str = unit_obj.name
                    elif hasattr(unit_obj, "abbreviation"):
                        unit_str = unit_obj.abbreviation
                    elif unit_obj is not None:
                        unit_str = str(unit_obj)
                    ingredient_map[name_key]["unit"] = unit_str
                
                # Track which days use this ingredient
                if day not in ingredient_map[name_key]["used_in_days"]:
                    ingredient_map[name_key]["used_in_days"].append(day)
        
        # Convert to ConsolidatedIngredient schema
        consolidated = {}
        for name_key, data in ingredient_map.items():
            consolidated[data["name"]] = ConsolidatedIngredient(
                name=data["name"],
                quantity=data["quantity"] if data["quantity"] > 0 else None,
                unit=data["unit"],
                used_in_days=data["used_in_days"],
            )
        
        return consolidated

    def _generate_substitution_suggestions(
        self,
        shopping_list: dict[str, ConsolidatedIngredient],
    ) -> list[SubstitutionSuggestion]:
        """
        Generate cheaper/seasonal ingredient substitution suggestions.
        
        For MVP, this uses a simple lookup table. Future versions could use:
        - Real-time pricing APIs
        - Seasonal availability data
        - Nutritional databases
        """
        substitutions = []
        
        # Simple substitution rules (MVP)
        substitution_rules = {
            "olive oil": {
                "alternative": "avocado oil",
                "reason": "higher smoke point, better for high-heat cooking",
                "savings": None,
            },
            "butter": {
                "alternative": "margarine",
                "reason": "cheaper alternative",
                "savings": 2.0,
            },
            "ground beef": {
                "alternative": "ground turkey",
                "reason": "cheaper and leaner",
                "savings": 3.0,
            },
            "salmon": {
                "alternative": "tilapia",
                "reason": "more affordable white fish",
                "savings": 5.0,
            },
        }
        
        for ingredient_name in shopping_list.keys():
            name_lower = ingredient_name.lower()
            
            for original, sub_data in substitution_rules.items():
                if original in name_lower:
                    substitutions.append(
                        SubstitutionSuggestion(
                            ingredient=ingredient_name,
                            reason=sub_data["reason"],
                            suggested_alternative=sub_data["alternative"],
                            estimated_savings=sub_data.get("savings"),
                        )
                    )
        
        return substitutions

    def _generate_cache_key(self, request: RandomizerRequest) -> str:
        """Generate cache key from request parameters"""
        # Simple cache key based on filters and start date
        filters_str = str(request.filters.model_dump_json())
        return f"{self.user_id}:{request.start_date}:{hash(filters_str)}"

    def _get_cached_result(self, cache_key: str) -> RandomizerResponse | None:
        """Retrieve cached result if still valid (within 5 minutes)"""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < timedelta(minutes=5):
                return result
        
        return None

    def _cache_result(self, cache_key: str, result: RandomizerResponse) -> None:
        """Cache result for 5 minutes"""
        self._cache[cache_key] = (result, datetime.now())
        
        # Simple cache cleanup: remove entries older than 10 minutes
        cutoff = datetime.now() - timedelta(minutes=10)
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items() if timestamp < cutoff
        ]
        for key in expired_keys:
            del self._cache[key]
