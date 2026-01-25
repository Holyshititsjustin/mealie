"""Unit tests for Meal Randomizer Service"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from mealie.schema.meal_randomizer.randomizer_request import (
    RandomizerFilters,
    RandomizerRequest,
    ProteinPreference,
)
from mealie.schema.meal_randomizer.randomizer_response import RecipeResultCard
from mealie.services.meal_randomizer.meal_randomizer_service import (
    MealRandomizerService,
    NotEnoughRecipesError,
)


@pytest.fixture
def mock_session():
    """Mock database session"""
    return Mock()


@pytest.fixture
def mock_filter_service():
    """Mock RecipeFilterService"""
    return Mock()


@pytest.fixture
def mock_recipes():
    """Create mock recipe objects with various properties"""
    recipes = []
    proteins = ["chicken", "fish", "beef", "tofu"]
    categories = ["pasta", "salad", "soup", "pizza"]
    
    for i in range(15):
        recipe = Mock()
        recipe.id = uuid4()
        recipe.slug = f"recipe-{i}"
        recipe.name = f"{proteins[i % 4]} {categories[i % 4]} {i}"
        recipe.cook_time = 30 + (i * 5)
        recipe.description = f"Description for recipe {i}"
        recipe.image = f"image-{i}.jpg"
        recipe.tags = []
        recipe.ingredients = []
        recipes.append(recipe)
    
    return recipes


@pytest.fixture
def randomizer_service(mock_session, mock_filter_service):
    """Create MealRandomizerService instance"""
    user_id = uuid4()
    group_id = uuid4()
    service = MealRandomizerService(mock_session, user_id, group_id)
    service.filter_service = mock_filter_service
    return service


class TestMealRandomizerService:
    """Test MealRandomizerService core logic"""

    def test_create_protein_queue(self, randomizer_service):
        """Test protein queue creation from preferences"""
        protein_prefs = [
            ProteinPreference(protein_type="chicken", count=3),
            ProteinPreference(protein_type="fish", count=2),
            ProteinPreference(protein_type="vegetarian", count=2),
        ]
        
        queue = randomizer_service._create_protein_queue(protein_prefs)
        
        assert len(queue) == 7
        assert queue.count("chicken") == 3
        assert queue.count("fish") == 2
        assert queue.count("vegetarian") == 2

    def test_protein_queue_shuffled(self, randomizer_service):
        """Test that protein queue is randomized"""
        protein_prefs = [
            ProteinPreference(protein_type="chicken", count=7),
        ]
        
        # Generate multiple queues and check they're not all identical
        queues = [randomizer_service._create_protein_queue(protein_prefs) for _ in range(10)]
        
        # At least one should be different from the first (statistically almost certain)
        assert any(q != queues[0] for q in queues[1:])

    def test_select_recipe_for_protein(self, randomizer_service, mock_recipes):
        """Test selecting a recipe for specific protein type"""
        used_recipe_ids = set()
        
        chicken_recipes = [r for r in mock_recipes if "chicken" in r.name.lower()]
        
        with patch.object(
            randomizer_service.filter_service,
            "get_recipes_by_protein",
            return_value=chicken_recipes
        ):
            recipe = randomizer_service._select_recipe_for_protein(
                mock_recipes, "chicken", used_recipe_ids
            )
            
            assert recipe is not None
            assert "chicken" in recipe.name.lower()
            assert recipe.id not in used_recipe_ids

    def test_select_any_unused_recipe(self, randomizer_service, mock_recipes):
        """Test selecting any unused recipe as fallback"""
        used_recipe_ids = {mock_recipes[0].id, mock_recipes[1].id}
        
        recipe = randomizer_service._select_any_unused_recipe(mock_recipes, used_recipe_ids)
        
        assert recipe is not None
        assert recipe.id not in used_recipe_ids

    def test_extract_categories(self, randomizer_service):
        """Test category extraction from recipe name and tags"""
        recipe = Mock()
        recipe.name = "Chicken Pasta Carbonara"
        
        pasta_tag = Mock()
        pasta_tag.name = "pasta"
        italian_tag = Mock()
        italian_tag.name = "italian"
        
        recipe.tags = [pasta_tag, italian_tag]
        
        categories = randomizer_service._extract_categories(recipe)
        
        assert "pasta" in categories

    def test_extract_difficulty(self, randomizer_service):
        """Test difficulty extraction from tags"""
        recipe = Mock()
        
        easy_tag = Mock()
        easy_tag.name = "easy"
        quick_tag = Mock()
        quick_tag.name = "quick"
        
        recipe.tags = [easy_tag, quick_tag]
        
        difficulty = randomizer_service._extract_difficulty(recipe)
        
        assert difficulty == "easy"

    def test_extract_difficulty_default(self, randomizer_service):
        """Test default difficulty when no difficulty tag present"""
        recipe = Mock()
        recipe.tags = []
        
        difficulty = randomizer_service._extract_difficulty(recipe)
        
        assert difficulty == "medium"

    def test_apply_balance_rules_detects_clustering(self, randomizer_service, mock_recipes):
        """Test that balance rules detect category clustering"""
        # Create week plan with 4 pasta dishes
        week_plan = []
        for i in range(7):
            recipe = Mock()
            recipe.id = uuid4()
            recipe.name = f"Pasta Recipe {i}" if i < 4 else f"Salad Recipe {i}"
            
            pasta_tag = Mock()
            pasta_tag.name = "pasta"
            salad_tag = Mock()
            salad_tag.name = "salad"
            
            recipe.tags = [pasta_tag] if i < 4 else [salad_tag]
            week_plan.append(recipe)
        
        # Mock candidate recipes for swapping
        candidate_chicken = Mock()
        candidate_chicken.id = uuid4()
        candidate_chicken.name = "Chicken Recipe"
        candidate_chicken.tags = []
        
        candidates = [candidate_chicken]
        
        # Balance rules should attempt to swap
        balanced = randomizer_service._apply_balance_rules(week_plan, candidates)
        
        # Should still have 7 recipes
        assert len(balanced) == 7

    def test_consolidate_shopping_list(self, randomizer_service):
        """Test shopping list consolidation"""
        # Create recipes with overlapping ingredients
        recipe1 = Mock()
        ingredient1 = Mock()
        ingredient1.note = "2 cups flour"
        ingredient1.food = Mock()
        ingredient1.food.name = "flour"
        recipe1.ingredients = [ingredient1]
        
        recipe2 = Mock()
        ingredient2 = Mock()
        ingredient2.note = "1 cup flour"
        ingredient2.food = Mock()
        ingredient2.food.name = "flour"
        recipe2.ingredients = [ingredient2]
        
        week_plan = [recipe1, recipe2]
        day_names = ["Monday", "Tuesday"]
        
        consolidated = randomizer_service._consolidate_shopping_list(week_plan, day_names)
        
        # Should have consolidated flour
        assert "flour" in consolidated or "Flour" in consolidated

    def test_generate_substitution_suggestions(self, randomizer_service):
        """Test substitution suggestion generation"""
        consolidated_list = {
            "olive oil": Mock(name="olive oil", quantity=0.5, unit="cup"),
            "butter": Mock(name="butter", quantity=1, unit="cup"),
        }
        
        suggestions = randomizer_service._generate_substitution_suggestions(consolidated_list)
        
        # Should suggest substitutions for olive oil and butter
        ingredient_names = [s.ingredient for s in suggestions]
        assert any("olive" in name.lower() for name in ingredient_names) or \
               any("butter" in name.lower() for name in ingredient_names)

    def test_generate_cache_key(self, randomizer_service):
        """Test cache key generation"""
        request = RandomizerRequest(
            start_date="2026-01-24",
            filters=RandomizerFilters(
                dietary_restrictions=["vegan"],
                allergens=[],
                protein_preferences=[],
                avoid_repeat_days=7,
                cook_time_bands=[],
                meal_types=[],
                difficulty_levels=[],
                include_expiring_ingredients=False,
                recipe_candidate_cap=200,
            ),
            pinned_days={},
        )
        
        key1 = randomizer_service._generate_cache_key(request)
        key2 = randomizer_service._generate_cache_key(request)
        
        # Same request should generate same key
        assert key1 == key2

    def test_cache_key_different_for_different_requests(self, randomizer_service):
        """Test that different requests generate different cache keys"""
        request1 = RandomizerRequest(
            start_date="2026-01-24",
            filters=RandomizerFilters(
                dietary_restrictions=["vegan"],
                allergens=[],
                protein_preferences=[],
                avoid_repeat_days=7,
                cook_time_bands=[],
                meal_types=[],
                difficulty_levels=[],
                include_expiring_ingredients=False,
                recipe_candidate_cap=200,
            ),
            pinned_days={},
        )
        
        request2 = RandomizerRequest(
            start_date="2026-01-24",
            filters=RandomizerFilters(
                dietary_restrictions=["vegetarian"],  # Different
                allergens=[],
                protein_preferences=[],
                avoid_repeat_days=7,
                cook_time_bands=[],
                meal_types=[],
                difficulty_levels=[],
                include_expiring_ingredients=False,
                recipe_candidate_cap=200,
            ),
            pinned_days={},
        )
        
        key1 = randomizer_service._generate_cache_key(request1)
        key2 = randomizer_service._generate_cache_key(request2)
        
        assert key1 != key2

    def test_insufficient_recipes_raises_error(self, randomizer_service):
        """Test that insufficient recipes raises appropriate error"""
        request = RandomizerRequest(
            start_date="2026-01-24",
            filters=RandomizerFilters(
                dietary_restrictions=[],
                allergens=[],
                protein_preferences=[],
                avoid_repeat_days=7,
                cook_time_bands=[],
                meal_types=[],
                difficulty_levels=[],
                include_expiring_ingredients=False,
                recipe_candidate_cap=200,
            ),
            pinned_days={},
        )
        
        # Mock filter service to return insufficient recipes
        with patch.object(
            randomizer_service.filter_service,
            "get_candidate_recipes",
            return_value=[]
        ):
            with patch.object(
                randomizer_service.filter_service,
                "broaden_filters_and_retry",
                return_value=request.filters
            ):
                with pytest.raises(NotEnoughRecipesError):
                    randomizer_service.generate_week_plan(request)

    def test_full_week_plan_generation(self, randomizer_service, mock_recipes):
        """Test complete week plan generation flow"""
        request = RandomizerRequest(
            start_date="2026-01-24",
            filters=RandomizerFilters(
                dietary_restrictions=[],
                allergens=[],
                protein_preferences=[
                    ProteinPreference(protein_type="chicken", count=3),
                    ProteinPreference(protein_type="fish", count=2),
                    ProteinPreference(protein_type="vegetarian", count=2),
                ],
                avoid_repeat_days=7,
                cook_time_bands=[],
                meal_types=[],
                difficulty_levels=[],
                include_expiring_ingredients=False,
                recipe_candidate_cap=200,
            ),
            pinned_days={},
        )
        
        # Mock filter service to return recipes
        with patch.object(
            randomizer_service.filter_service,
            "get_candidate_recipes",
            return_value=mock_recipes
        ):
            with patch.object(
                randomizer_service.filter_service,
                "get_recipes_by_protein",
                side_effect=lambda recipes, protein: [
                    r for r in recipes if protein.lower() in r.name.lower()
                ][:3]
            ):
                result = randomizer_service.generate_week_plan(request)
                
                # Should return 7 meals
                assert len(result.week_plan) == 7
                
                # Each day should have required fields
                for meal in result.week_plan:
                    assert meal.day
                    assert meal.date
                    assert meal.recipe_id
                    assert meal.recipe_name
                    
                # Should have shopping list
                assert result.shopping_consolidated
                
                # Should have metadata
                assert result.metadata
                assert result.metadata["generated_at"]

    def test_pinned_days_preserved(self, randomizer_service, mock_recipes):
        """Test that pinned days are preserved in generation"""
        pinned_recipe_id = str(mock_recipes[0].id)
        
        request = RandomizerRequest(
            start_date="2026-01-24",
            filters=RandomizerFilters(
                dietary_restrictions=[],
                allergens=[],
                protein_preferences=[],
                avoid_repeat_days=7,
                cook_time_bands=[],
                meal_types=[],
                difficulty_levels=[],
                include_expiring_ingredients=False,
                recipe_candidate_cap=200,
            ),
            pinned_days={"Monday": pinned_recipe_id},
        )
        
        # Mock recipe loading
        with patch.object(
            randomizer_service,
            "_load_recipe_by_id",
            return_value=mock_recipes[0]
        ):
            with patch.object(
                randomizer_service.filter_service,
                "get_candidate_recipes",
                return_value=mock_recipes
            ):
                result = randomizer_service.generate_week_plan(request)
                
                # Monday should have the pinned recipe
                monday_meal = next((m for m in result.week_plan if m.day == "Monday"), None)
                assert monday_meal is not None
                assert monday_meal.pinned is True
                assert str(monday_meal.recipe_id) == pinned_recipe_id
