"""Unit tests for Recipe Filter Service"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from mealie.schema.meal_randomizer.randomizer_request import RandomizerFilters, ProteinPreference
from mealie.services.meal_randomizer.recipe_filter_service import RecipeFilterService


@pytest.fixture
def mock_session():
    """Mock database session"""
    return Mock()


@pytest.fixture
def mock_recipes():
    """Create mock recipe objects"""
    recipes = []
    for i in range(20):
        recipe = Mock()
        recipe.id = uuid4()
        recipe.name = f"Recipe {i}"
        recipe.cook_time = 30 + (i * 5)
        recipe.description = "Test description"
        recipe.tags = []
        recipe.ingredients = []
        recipes.append(recipe)
    return recipes


@pytest.fixture
def filter_service(mock_session):
    """Create RecipeFilterService instance"""
    user_id = uuid4()
    group_id = uuid4()
    return RecipeFilterService(mock_session, user_id, group_id)


class TestRecipeFilterService:
    """Test RecipeFilterService filtering logic"""

    def test_empty_filters_returns_all_recipes(self, filter_service, mock_recipes):
        """Test that empty filters return all candidate recipes"""
        filters = RandomizerFilters(
            dietary_restrictions=[],
            allergens=[],
            protein_preferences=[],
            avoid_repeat_days=7,
            cook_time_bands=[],
            meal_types=[],
            difficulty_levels=[],
            include_expiring_ingredients=False,
            recipe_candidate_cap=200,
        )

        with patch.object(filter_service, "_get_all_recipes", return_value=mock_recipes):
            result = filter_service.get_candidate_recipes(filters)
            assert len(result) <= len(mock_recipes)

    def test_dietary_restriction_filtering(self, filter_service):
        """Test filtering by dietary restrictions"""
        vegetarian_tag = Mock()
        vegetarian_tag.name = "vegetarian"
        
        recipe1 = Mock()
        recipe1.tags = [vegetarian_tag]
        recipe1.name = "Vegetarian Recipe"
        
        recipe2 = Mock()
        recipe2.tags = []
        recipe2.name = "Non-vegetarian Recipe"
        
        recipes = [recipe1, recipe2]
        
        filters = RandomizerFilters(
            dietary_restrictions=["vegetarian"],
            allergens=[],
            protein_preferences=[],
            avoid_repeat_days=7,
            cook_time_bands=[],
            meal_types=[],
            difficulty_levels=[],
            include_expiring_ingredients=False,
            recipe_candidate_cap=200,
        )

        filtered = filter_service._apply_dietary_restrictions(recipes, filters.dietary_restrictions)
        assert len(filtered) == 1
        assert filtered[0].name == "Vegetarian Recipe"

    def test_allergen_exclusion(self, filter_service):
        """Test exclusion of recipes with allergens"""
        nuts_tag = Mock()
        nuts_tag.name = "nuts"
        
        recipe1 = Mock()
        recipe1.tags = [nuts_tag]
        recipe1.name = "Recipe with Nuts"
        
        recipe2 = Mock()
        recipe2.tags = []
        recipe2.name = "Nut-free Recipe"
        
        recipes = [recipe1, recipe2]
        
        filters_allergens = ["nuts"]
        
        filtered = filter_service._apply_allergen_exclusions(recipes, filters_allergens)
        assert len(filtered) == 1
        assert filtered[0].name == "Nut-free Recipe"

    def test_cook_time_filtering(self, filter_service):
        """Test filtering by cook time bands"""
        recipe_quick = Mock()
        recipe_quick.cook_time = 10
        recipe_quick.name = "Quick Recipe"
        
        recipe_medium = Mock()
        recipe_medium.cook_time = 25
        recipe_medium.name = "Medium Recipe"
        
        recipe_long = Mock()
        recipe_long.cook_time = 70
        recipe_long.name = "Long Recipe"
        
        recipes = [recipe_quick, recipe_medium, recipe_long]
        
        # Filter for 0-15 and 15-30 minute recipes
        cook_time_bands = ["0-15", "15-30"]
        
        filtered = filter_service._apply_cook_time_filters(recipes, cook_time_bands)
        assert len(filtered) == 2
        assert recipe_long not in filtered

    def test_exclude_recent_recipes(self, filter_service):
        """Test exclusion of recently used recipes"""
        recipe1 = Mock()
        recipe1.id = uuid4()
        recipe1.name = "Recent Recipe"
        
        recipe2 = Mock()
        recipe2.id = uuid4()
        recipe2.name = "Old Recipe"
        
        recipes = [recipe1, recipe2]
        
        # Mock recent meal containing recipe1
        recent_meal = Mock()
        recent_meal.recipe_id = recipe1.id
        recent_meal.entry_date = datetime.now() - timedelta(days=3)
        
        with patch.object(filter_service, "_get_recent_meals", return_value=[recent_meal]):
            filtered = filter_service._exclude_recent_recipes(recipes, avoid_repeat_days=7)
            assert len(filtered) == 1
            assert filtered[0].name == "Old Recipe"

    def test_exclude_never_again_recipes(self, filter_service):
        """Test exclusion of 'never again' rated recipes"""
        recipe1 = Mock()
        recipe1.id = uuid4()
        recipe1.name = "Never Again Recipe"
        
        recipe2 = Mock()
        recipe2.id = uuid4()
        recipe2.name = "Good Recipe"
        
        recipes = [recipe1, recipe2]
        
        # Mock rating for recipe1 as 'never_again'
        rating = Mock()
        rating.recipe_id = recipe1.id
        rating.rating = "never_again"
        
        with patch.object(filter_service, "_get_never_again_ratings", return_value=[rating]):
            filtered = filter_service._exclude_never_again_recipes(recipes)
            assert len(filtered) == 1
            assert filtered[0].name == "Good Recipe"

    def test_sort_by_user_preference(self, filter_service):
        """Test sorting recipes by user ratings"""
        recipe_loved = Mock()
        recipe_loved.id = uuid4()
        recipe_loved.name = "Loved Recipe"
        
        recipe_neutral = Mock()
        recipe_neutral.id = uuid4()
        recipe_neutral.name = "Neutral Recipe"
        
        recipe_disliked = Mock()
        recipe_disliked.id = uuid4()
        recipe_disliked.name = "Disliked Recipe"
        
        recipes = [recipe_disliked, recipe_neutral, recipe_loved]
        
        # Mock ratings
        rating_up = Mock()
        rating_up.recipe_id = recipe_loved.id
        rating_up.rating = "up"
        
        rating_down = Mock()
        rating_down.recipe_id = recipe_disliked.id
        rating_down.rating = "down"
        
        with patch.object(filter_service, "_get_all_ratings", return_value=[rating_up, rating_down]):
            sorted_recipes = filter_service._sort_by_user_preference(recipes)
            # Loved should be first, disliked should be last
            assert sorted_recipes[0].name == "Loved Recipe"
            assert sorted_recipes[-1].name == "Disliked Recipe"

    def test_recipe_candidate_cap(self, filter_service, mock_recipes):
        """Test that recipe candidate cap limits results"""
        filters = RandomizerFilters(
            dietary_restrictions=[],
            allergens=[],
            protein_preferences=[],
            avoid_repeat_days=7,
            cook_time_bands=[],
            meal_types=[],
            difficulty_levels=[],
            include_expiring_ingredients=False,
            recipe_candidate_cap=10,  # Cap at 10
        )

        with patch.object(filter_service, "_get_all_recipes", return_value=mock_recipes):
            result = filter_service.get_candidate_recipes(filters)
            assert len(result) <= 10

    def test_get_recipes_by_protein(self, filter_service):
        """Test filtering recipes by protein type"""
        chicken_recipe = Mock()
        chicken_recipe.name = "Chicken Parmesan"
        chicken_recipe.description = "Delicious chicken dish"
        chicken_recipe.ingredients = []
        chicken_recipe.tags = []
        
        fish_recipe = Mock()
        fish_recipe.name = "Grilled Salmon"
        fish_recipe.description = "Fresh salmon"
        fish_recipe.ingredients = []
        fish_recipe.tags = []
        
        recipes = [chicken_recipe, fish_recipe]
        
        chicken_results = filter_service.get_recipes_by_protein(recipes, "chicken")
        assert len(chicken_results) == 1
        assert chicken_results[0].name == "Chicken Parmesan"
        
        fish_results = filter_service.get_recipes_by_protein(recipes, "fish")
        assert len(fish_results) == 1
        assert fish_results[0].name == "Grilled Salmon"

    def test_broaden_filters_and_retry(self, filter_service):
        """Test filter broadening when not enough recipes found"""
        filters = RandomizerFilters(
            dietary_restrictions=["vegan"],
            allergens=["nuts"],
            protein_preferences=[],
            avoid_repeat_days=14,
            cook_time_bands=["0-15"],
            meal_types=["quick_weeknight"],
            difficulty_levels=["easy"],
            include_expiring_ingredients=False,
            recipe_candidate_cap=200,
        )

        # First broadening: remove difficulty
        broadened1 = filter_service.broaden_filters_and_retry(filters)
        assert len(broadened1.difficulty_levels) == 0
        assert broadened1.cook_time_bands == ["0-15"]
        
        # Second broadening: remove cook_time
        broadened2 = filter_service.broaden_filters_and_retry(broadened1)
        assert len(broadened2.cook_time_bands) == 0
        assert broadened2.meal_types == ["quick_weeknight"]
        
        # Third broadening: remove meal_types
        broadened3 = filter_service.broaden_filters_and_retry(broadened2)
        assert len(broadened3.meal_types) == 0
        assert broadened3.avoid_repeat_days == 14
        
        # Fourth broadening: reduce repeat window
        broadened4 = filter_service.broaden_filters_and_retry(broadened3)
        assert broadened4.avoid_repeat_days == 7

    def test_multiple_dietary_restrictions(self, filter_service):
        """Test recipes must match ALL dietary restrictions"""
        vegan_tag = Mock()
        vegan_tag.name = "vegan"
        gluten_free_tag = Mock()
        gluten_free_tag.name = "gluten_free"
        
        recipe1 = Mock()
        recipe1.tags = [vegan_tag, gluten_free_tag]
        recipe1.name = "Vegan and Gluten Free"
        
        recipe2 = Mock()
        recipe2.tags = [vegan_tag]
        recipe2.name = "Vegan Only"
        
        recipe3 = Mock()
        recipe3.tags = [gluten_free_tag]
        recipe3.name = "Gluten Free Only"
        
        recipes = [recipe1, recipe2, recipe3]
        
        dietary_restrictions = ["vegan", "gluten_free"]
        
        filtered = filter_service._apply_dietary_restrictions(recipes, dietary_restrictions)
        assert len(filtered) == 1
        assert filtered[0].name == "Vegan and Gluten Free"
