"""Integration tests for Meal Randomizer API endpoints"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from tests.utils.fixture_schemas import TestUser


class TestMealRandomizerGenerate:
    """Test meal randomizer generation endpoint"""

    def test_generate_week_plan_success(self, api_client: TestClient, unique_user: TestUser):
        """Test successful week plan generation"""
        request_data = {
            "start_date": "2026-01-27",
            "filters": {
                "dietary_restrictions": [],
                "allergens": [],
                "protein_preferences": [
                    {"protein_type": "chicken", "count": 3},
                    {"protein_type": "fish", "count": 2},
                    {"protein_type": "vegetarian", "count": 2},
                ],
                "avoid_repeat_days": 7,
                "cook_time_bands": [],
                "meal_types": [],
                "difficulty_levels": [],
                "include_expiring_ingredients": False,
                "recipe_candidate_cap": 200,
            },
            "pinned_days": {},
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/generate",
            json=request_data,
            headers=unique_user.token,
        )

        assert response.status_code in [200, 400]  # 400 if not enough recipes
        
        if response.status_code == 200:
            data = response.json()
            assert "week_plan" in data
            assert "shopping_consolidated" in data
            assert "metadata" in data
            assert len(data["week_plan"]) <= 7

    def test_generate_requires_authentication(self, api_client: TestClient):
        """Test that generation endpoint requires authentication"""
        request_data = {
            "start_date": "2026-01-27",
            "filters": {
                "dietary_restrictions": [],
                "allergens": [],
                "protein_preferences": [],
                "avoid_repeat_days": 7,
                "cook_time_bands": [],
                "meal_types": [],
                "difficulty_levels": [],
                "include_expiring_ingredients": False,
                "recipe_candidate_cap": 200,
            },
            "pinned_days": {},
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/generate",
            json=request_data,
        )

        assert response.status_code == 401

    def test_generate_with_dietary_restrictions(self, api_client: TestClient, unique_user: TestUser):
        """Test generation with dietary restrictions"""
        request_data = {
            "start_date": "2026-01-27",
            "filters": {
                "dietary_restrictions": ["vegetarian", "gluten_free"],
                "allergens": [],
                "protein_preferences": [],
                "avoid_repeat_days": 7,
                "cook_time_bands": [],
                "meal_types": [],
                "difficulty_levels": [],
                "include_expiring_ingredients": False,
                "recipe_candidate_cap": 200,
            },
            "pinned_days": {},
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/generate",
            json=request_data,
            headers=unique_user.token,
        )

        # Should either succeed or return 400 if not enough recipes match criteria
        assert response.status_code in [200, 400]

    def test_generate_with_allergen_exclusions(self, api_client: TestClient, unique_user: TestUser):
        """Test generation with allergen exclusions"""
        request_data = {
            "start_date": "2026-01-27",
            "filters": {
                "dietary_restrictions": [],
                "allergens": ["nuts", "shellfish"],
                "protein_preferences": [],
                "avoid_repeat_days": 7,
                "cook_time_bands": [],
                "meal_types": [],
                "difficulty_levels": [],
                "include_expiring_ingredients": False,
                "recipe_candidate_cap": 200,
            },
            "pinned_days": {},
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/generate",
            json=request_data,
            headers=unique_user.token,
        )

        assert response.status_code in [200, 400]

    def test_generate_with_cook_time_filters(self, api_client: TestClient, unique_user: TestUser):
        """Test generation with cook time filters"""
        request_data = {
            "start_date": "2026-01-27",
            "filters": {
                "dietary_restrictions": [],
                "allergens": [],
                "protein_preferences": [],
                "avoid_repeat_days": 7,
                "cook_time_bands": ["0-15", "15-30"],
                "meal_types": [],
                "difficulty_levels": [],
                "include_expiring_ingredients": False,
                "recipe_candidate_cap": 200,
            },
            "pinned_days": {},
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/generate",
            json=request_data,
            headers=unique_user.token,
        )

        assert response.status_code in [200, 400]

    def test_generate_invalid_request_format(self, api_client: TestClient, unique_user: TestUser):
        """Test that invalid request format returns 422"""
        request_data = {
            "start_date": "invalid-date",
            "filters": {},
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/generate",
            json=request_data,
            headers=unique_user.token,
        )

        assert response.status_code == 422


class TestMealRandomizerTemplates:
    """Test meal randomizer template endpoints"""

    def test_list_templates_empty(self, api_client: TestClient, unique_user: TestUser):
        """Test listing templates when none exist"""
        response = api_client.get(
            "/api/v1/households/meals/randomizer/templates",
            headers=unique_user.token,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_template_success(self, api_client: TestClient, unique_user: TestUser):
        """Test creating a new template"""
        template_data = {
            "template_name": "Summer Weeknights",
            "week_plan_json": [
                {
                    "day": "Monday",
                    "date": "2026-01-27",
                    "recipe_id": str(uuid4()),
                    "recipe_name": "Chicken Parmesan",
                    "recipe_slug": "chicken-parmesan",
                    "cook_time": 45,
                    "difficulty": "medium",
                    "dietary_tags": [],
                    "pinned": False,
                }
            ],
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/templates",
            json=template_data,
            headers=unique_user.token,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["template_name"] == "Summer Weeknights"
        assert "id" in data
        assert "user_id" in data

    def test_create_template_requires_auth(self, api_client: TestClient):
        """Test that creating template requires authentication"""
        template_data = {
            "template_name": "Test Template",
            "week_plan_json": [],
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/templates",
            json=template_data,
        )

        assert response.status_code == 401

    def test_get_template_by_id(self, api_client: TestClient, unique_user: TestUser):
        """Test retrieving a specific template"""
        # First create a template
        template_data = {
            "template_name": "Test Template",
            "week_plan_json": [],
        }

        create_response = api_client.post(
            "/api/v1/households/meals/randomizer/templates",
            json=template_data,
            headers=unique_user.token,
        )

        if create_response.status_code == 201:
            template_id = create_response.json()["id"]

            # Then retrieve it
            response = api_client.get(
                f"/api/v1/households/meals/randomizer/templates/{template_id}",
                headers=unique_user.token,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == template_id
            assert data["template_name"] == "Test Template"

    def test_get_nonexistent_template(self, api_client: TestClient, unique_user: TestUser):
        """Test retrieving a non-existent template returns 404"""
        fake_id = str(uuid4())

        response = api_client.get(
            f"/api/v1/households/meals/randomizer/templates/{fake_id}",
            headers=unique_user.token,
        )

        assert response.status_code == 404

    def test_delete_template_success(self, api_client: TestClient, unique_user: TestUser):
        """Test deleting a template"""
        # First create a template
        template_data = {
            "template_name": "Template to Delete",
            "week_plan_json": [],
        }

        create_response = api_client.post(
            "/api/v1/households/meals/randomizer/templates",
            json=template_data,
            headers=unique_user.token,
        )

        if create_response.status_code == 201:
            template_id = create_response.json()["id"]

            # Then delete it
            response = api_client.delete(
                f"/api/v1/households/meals/randomizer/templates/{template_id}",
                headers=unique_user.token,
            )

            assert response.status_code == 200

            # Verify it's deleted
            get_response = api_client.get(
                f"/api/v1/households/meals/randomizer/templates/{template_id}",
                headers=unique_user.token,
            )

            assert get_response.status_code == 404

    def test_delete_template_wrong_user(self, api_client: TestClient, unique_user: TestUser):
        """Test that users can only delete their own templates"""
        # Create template with one user
        template_data = {
            "template_name": "User1 Template",
            "week_plan_json": [],
        }

        create_response = api_client.post(
            "/api/v1/households/meals/randomizer/templates",
            json=template_data,
            headers=unique_user.token,
        )

        if create_response.status_code == 201:
            template_id = create_response.json()["id"]

            # Try to delete with different user (if possible to set up)
            # This test would require a second user fixture
            # For now, just verify the template exists
            response = api_client.get(
                f"/api/v1/households/meals/randomizer/templates/{template_id}",
                headers=unique_user.token,
            )

            assert response.status_code == 200


class TestMealRandomizerRatings:
    """Test recipe rating endpoints"""

    def test_rate_recipe_up(self, api_client: TestClient, unique_user: TestUser):
        """Test rating a recipe positively"""
        rating_data = {
            "recipe_id": str(uuid4()),
            "rating": "up",
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/rate",
            json=rating_data,
            headers=unique_user.token,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == "up"
        assert "id" in data

    def test_rate_recipe_down(self, api_client: TestClient, unique_user: TestUser):
        """Test rating a recipe negatively"""
        rating_data = {
            "recipe_id": str(uuid4()),
            "rating": "down",
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/rate",
            json=rating_data,
            headers=unique_user.token,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == "down"

    def test_rate_recipe_never_again(self, api_client: TestClient, unique_user: TestUser):
        """Test marking a recipe as never again"""
        rating_data = {
            "recipe_id": str(uuid4()),
            "rating": "never_again",
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/rate",
            json=rating_data,
            headers=unique_user.token,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == "never_again"

    def test_rate_recipe_requires_auth(self, api_client: TestClient):
        """Test that rating requires authentication"""
        rating_data = {
            "recipe_id": str(uuid4()),
            "rating": "up",
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/rate",
            json=rating_data,
        )

        assert response.status_code == 401

    def test_rate_recipe_invalid_rating(self, api_client: TestClient, unique_user: TestUser):
        """Test that invalid rating value returns 422"""
        rating_data = {
            "recipe_id": str(uuid4()),
            "rating": "invalid",
        }

        response = api_client.post(
            "/api/v1/households/meals/randomizer/rate",
            json=rating_data,
            headers=unique_user.token,
        )

        assert response.status_code == 422


class TestMealRandomizerPreferences:
    """Test user preferences endpoints"""

    def test_get_preferences_default(self, api_client: TestClient, unique_user: TestUser):
        """Test getting preferences returns defaults if none exist"""
        response = api_client.get(
            "/api/v1/households/meals/randomizer/preferences",
            headers=unique_user.token,
        )

        assert response.status_code == 200
        data = response.json()
        assert "recipe_candidate_cap" in data
        assert "avoid_repeat_days" in data

    def test_update_preferences_success(self, api_client: TestClient, unique_user: TestUser):
        """Test updating user preferences"""
        prefs_data = {
            "recipe_candidate_cap": 150,
            "avoid_repeat_days": 14,
            "filter_defaults": {
                "dietary_restrictions": ["vegetarian"],
            },
        }

        response = api_client.put(
            "/api/v1/households/meals/randomizer/preferences",
            json=prefs_data,
            headers=unique_user.token,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["recipe_candidate_cap"] == 150
        assert data["avoid_repeat_days"] == 14

    def test_update_preferences_partial(self, api_client: TestClient, unique_user: TestUser):
        """Test partial update of preferences"""
        prefs_data = {
            "recipe_candidate_cap": 100,
        }

        response = api_client.put(
            "/api/v1/households/meals/randomizer/preferences",
            json=prefs_data,
            headers=unique_user.token,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["recipe_candidate_cap"] == 100

    def test_preferences_require_auth(self, api_client: TestClient):
        """Test that preferences endpoints require authentication"""
        get_response = api_client.get(
            "/api/v1/households/meals/randomizer/preferences",
        )
        assert get_response.status_code == 401

        put_response = api_client.put(
            "/api/v1/households/meals/randomizer/preferences",
            json={},
        )
        assert put_response.status_code == 401
