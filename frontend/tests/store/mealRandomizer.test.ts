/**
 * Unit tests for Vuex store module - mealRandomizer
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createStore } from "vuex";
import mealRandomizerModule from "~/store/mealRandomizer";
import type { 
  MealPlanRequest, 
  WeekPlanResult, 
  MealPlanTemplate,
  UserPreferences 
} from "~/types/meal-randomizer";

// Mock axios
const mockAxios = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
};

describe("Vuex mealRandomizer Store Module", () => {
  let store: any;

  beforeEach(() => {
    vi.clearAllMocks();
    
    store = createStore({
      modules: {
        mealRandomizer: {
          ...mealRandomizerModule,
          namespaced: true,
        },
      },
    });

    // Inject mock axios into store
    store.$axios = mockAxios;
  });

  describe("State", () => {
    it("initializes with default state", () => {
      const state = store.state.mealRandomizer;

      expect(state.currentPlan).toBeNull();
      expect(state.templates).toEqual([]);
      expect(state.userPreferences).toBeNull();
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe("Mutations", () => {
    it("SET_CURRENT_PLAN updates current plan", () => {
      const mockPlan: WeekPlanResult = {
        week_plan: [],
        shopping_consolidated: {},
        substitution_suggestions: [],
        metadata: {
          generated_at: "2026-01-24T10:00:00Z",
          generation_method: "random",
        },
        is_cached: false,
      };

      store.commit("mealRandomizer/SET_CURRENT_PLAN", mockPlan);

      expect(store.state.mealRandomizer.currentPlan).toEqual(mockPlan);
    });

    it("SET_TEMPLATES updates templates list", () => {
      const mockTemplates: MealPlanTemplate[] = [
        {
          id: "1",
          user_id: "user-123",
          template_name: "Test Template",
          week_plan_json: "{}",
          recipe_names: ["Recipe 1"],
          created_at: "2026-01-24T10:00:00Z",
          updated_at: "2026-01-24T10:00:00Z",
        },
      ];

      store.commit("mealRandomizer/SET_TEMPLATES", mockTemplates);

      expect(store.state.mealRandomizer.templates).toEqual(mockTemplates);
    });

    it("SET_USER_PREFERENCES updates preferences", () => {
      const mockPreferences: UserPreferences = {
        default_protein_preferences: {
          beef: 2,
          pork: 1,
          chicken: 2,
          fish: 1,
          vegetarian: 1,
        },
        default_dietary_restrictions: ["gluten_free"],
        default_allergen_exclusions: ["peanuts"],
        default_cook_time_bands: ["0-15", "15-30"],
        default_avoid_repeat_days: 7,
        never_again_recipe_ids: ["recipe-123"],
      };

      store.commit("mealRandomizer/SET_USER_PREFERENCES", mockPreferences);

      expect(store.state.mealRandomizer.userPreferences).toEqual(mockPreferences);
    });

    it("SET_LOADING updates loading state", () => {
      store.commit("mealRandomizer/SET_LOADING", true);
      expect(store.state.mealRandomizer.loading).toBe(true);

      store.commit("mealRandomizer/SET_LOADING", false);
      expect(store.state.mealRandomizer.loading).toBe(false);
    });

    it("SET_ERROR updates error state", () => {
      const error = "Failed to generate plan";

      store.commit("mealRandomizer/SET_ERROR", error);

      expect(store.state.mealRandomizer.error).toBe(error);
    });

    it("CLEAR_ERROR clears error state", () => {
      store.commit("mealRandomizer/SET_ERROR", "Some error");
      store.commit("mealRandomizer/CLEAR_ERROR");

      expect(store.state.mealRandomizer.error).toBeNull();
    });

    it("ADD_TEMPLATE adds template to list", () => {
      const mockTemplate: MealPlanTemplate = {
        id: "1",
        user_id: "user-123",
        template_name: "New Template",
        week_plan_json: "{}",
        recipe_names: ["Recipe 1"],
        created_at: "2026-01-24T10:00:00Z",
        updated_at: "2026-01-24T10:00:00Z",
      };

      store.commit("mealRandomizer/ADD_TEMPLATE", mockTemplate);

      expect(store.state.mealRandomizer.templates).toContainEqual(mockTemplate);
    });

    it("REMOVE_TEMPLATE removes template from list", () => {
      const mockTemplates: MealPlanTemplate[] = [
        {
          id: "1",
          user_id: "user-123",
          template_name: "Template 1",
          week_plan_json: "{}",
          recipe_names: [],
          created_at: "2026-01-24T10:00:00Z",
          updated_at: "2026-01-24T10:00:00Z",
        },
        {
          id: "2",
          user_id: "user-123",
          template_name: "Template 2",
          week_plan_json: "{}",
          recipe_names: [],
          created_at: "2026-01-24T10:00:00Z",
          updated_at: "2026-01-24T10:00:00Z",
        },
      ];

      store.commit("mealRandomizer/SET_TEMPLATES", mockTemplates);
      store.commit("mealRandomizer/REMOVE_TEMPLATE", "1");

      expect(store.state.mealRandomizer.templates).toHaveLength(1);
      expect(store.state.mealRandomizer.templates[0].id).toBe("2");
    });
  });

  describe("Getters", () => {
    it("currentPlan returns current plan", () => {
      const mockPlan: WeekPlanResult = {
        week_plan: [],
        shopping_consolidated: {},
        substitution_suggestions: [],
        metadata: {
          generated_at: "2026-01-24T10:00:00Z",
          generation_method: "random",
        },
        is_cached: false,
      };

      store.commit("mealRandomizer/SET_CURRENT_PLAN", mockPlan);

      const currentPlan = store.getters["mealRandomizer/currentPlan"];
      expect(currentPlan).toEqual(mockPlan);
    });

    it("templates returns all templates", () => {
      const mockTemplates: MealPlanTemplate[] = [
        {
          id: "1",
          user_id: "user-123",
          template_name: "Template 1",
          week_plan_json: "{}",
          recipe_names: [],
          created_at: "2026-01-24T10:00:00Z",
          updated_at: "2026-01-24T10:00:00Z",
        },
      ];

      store.commit("mealRandomizer/SET_TEMPLATES", mockTemplates);

      const templates = store.getters["mealRandomizer/templates"];
      expect(templates).toEqual(mockTemplates);
    });

    it("isLoading returns loading state", () => {
      store.commit("mealRandomizer/SET_LOADING", true);

      const isLoading = store.getters["mealRandomizer/isLoading"];
      expect(isLoading).toBe(true);
    });

    it("hasError returns true when error exists", () => {
      store.commit("mealRandomizer/SET_ERROR", "Error message");

      const hasError = store.getters["mealRandomizer/hasError"];
      expect(hasError).toBe(true);
    });

    it("hasError returns false when no error", () => {
      store.commit("mealRandomizer/CLEAR_ERROR");

      const hasError = store.getters["mealRandomizer/hasError"];
      expect(hasError).toBe(false);
    });

    it("errorMessage returns error message", () => {
      const errorMsg = "Failed to load";
      store.commit("mealRandomizer/SET_ERROR", errorMsg);

      const errorMessage = store.getters["mealRandomizer/errorMessage"];
      expect(errorMessage).toBe(errorMsg);
    });
  });

  describe("Actions", () => {
    it("generatePlan calls API and commits result", async () => {
      const mockRequest: MealPlanRequest = {
        filters: {
          dietary_restrictions: [],
          allergen_exclusions: [],
          preferred_proteins: [],
          cook_time_bands: [],
          meal_types: [],
          recipe_candidate_cap: 200,
          avoid_repeat_days: 7,
        },
        protein_preferences: {
          beef: 2,
          pork: 1,
          chicken: 2,
          fish: 1,
          vegetarian: 1,
        },
        pinned_days: {},
      };

      const mockResponse: WeekPlanResult = {
        week_plan: [],
        shopping_consolidated: {},
        substitution_suggestions: [],
        metadata: {
          generated_at: "2026-01-24T10:00:00Z",
          generation_method: "random",
        },
        is_cached: false,
      };

      mockAxios.post.mockResolvedValue({ data: mockResponse });

      await store.dispatch("mealRandomizer/generatePlan", { 
        axios: mockAxios, 
        request: mockRequest 
      });

      expect(mockAxios.post).toHaveBeenCalledWith(
        "/api/v1/households/meals/randomizer/generate",
        mockRequest,
      );
      expect(store.state.mealRandomizer.currentPlan).toEqual(mockResponse);
    });

    it("fetchTemplates calls API and commits templates", async () => {
      const mockTemplates: MealPlanTemplate[] = [
        {
          id: "1",
          user_id: "user-123",
          template_name: "Template 1",
          week_plan_json: "{}",
          recipe_names: [],
          created_at: "2026-01-24T10:00:00Z",
          updated_at: "2026-01-24T10:00:00Z",
        },
      ];

      mockAxios.get.mockResolvedValue({ data: mockTemplates });

      await store.dispatch("mealRandomizer/fetchTemplates", { axios: mockAxios });

      expect(mockAxios.get).toHaveBeenCalledWith(
        "/api/v1/households/meals/randomizer/templates",
      );
      expect(store.state.mealRandomizer.templates).toEqual(mockTemplates);
    });

    it("saveTemplate calls API and adds template", async () => {
      const mockTemplate: MealPlanTemplate = {
        id: "1",
        user_id: "user-123",
        template_name: "New Template",
        week_plan_json: "{}",
        recipe_names: [],
        created_at: "2026-01-24T10:00:00Z",
        updated_at: "2026-01-24T10:00:00Z",
      };

      mockAxios.post.mockResolvedValue({ data: mockTemplate });

      await store.dispatch("mealRandomizer/saveTemplate", {
        axios: mockAxios,
        template: mockTemplate,
      });

      expect(mockAxios.post).toHaveBeenCalledWith(
        "/api/v1/households/meals/randomizer/templates",
        mockTemplate,
      );
      expect(store.state.mealRandomizer.templates).toContainEqual(mockTemplate);
    });

    it("deleteTemplate calls API and removes template", async () => {
      const mockTemplates: MealPlanTemplate[] = [
        {
          id: "1",
          user_id: "user-123",
          template_name: "Template 1",
          week_plan_json: "{}",
          recipe_names: [],
          created_at: "2026-01-24T10:00:00Z",
          updated_at: "2026-01-24T10:00:00Z",
        },
      ];

      store.commit("mealRandomizer/SET_TEMPLATES", mockTemplates);

      mockAxios.delete.mockResolvedValue({});

      await store.dispatch("mealRandomizer/deleteTemplate", {
        axios: mockAxios,
        templateId: "1",
      });

      expect(mockAxios.delete).toHaveBeenCalledWith(
        "/api/v1/households/meals/randomizer/templates/1",
      );
      expect(store.state.mealRandomizer.templates).toHaveLength(0);
    });

    it("rateRecipe calls API", async () => {
      mockAxios.post.mockResolvedValue({});

      await store.dispatch("mealRandomizer/rateRecipe", {
        axios: mockAxios,
        recipeId: "recipe-123",
        rating: "up",
      });

      expect(mockAxios.post).toHaveBeenCalledWith(
        "/api/v1/households/meals/randomizer/ratings",
        {
          recipe_id: "recipe-123",
          rating: "up",
        },
      );
    });

    it("fetchUserPreferences calls API and commits preferences", async () => {
      const mockPreferences: UserPreferences = {
        default_protein_preferences: {
          beef: 2,
          pork: 1,
          chicken: 2,
          fish: 1,
          vegetarian: 1,
        },
        default_dietary_restrictions: [],
        default_allergen_exclusions: [],
        default_cook_time_bands: [],
        default_avoid_repeat_days: 7,
        never_again_recipe_ids: [],
      };

      mockAxios.get.mockResolvedValue({ data: mockPreferences });

      await store.dispatch("mealRandomizer/fetchUserPreferences", { axios: mockAxios });

      expect(mockAxios.get).toHaveBeenCalledWith(
        "/api/v1/households/meals/randomizer/preferences",
      );
      expect(store.state.mealRandomizer.userPreferences).toEqual(mockPreferences);
    });

    it("updateUserPreferences calls API and commits new preferences", async () => {
      const mockPreferences: UserPreferences = {
        default_protein_preferences: {
          beef: 3,
          pork: 1,
          chicken: 2,
          fish: 1,
          vegetarian: 0,
        },
        default_dietary_restrictions: ["gluten_free"],
        default_allergen_exclusions: [],
        default_cook_time_bands: [],
        default_avoid_repeat_days: 14,
        never_again_recipe_ids: [],
      };

      mockAxios.put.mockResolvedValue({ data: mockPreferences });

      await store.dispatch("mealRandomizer/updateUserPreferences", {
        axios: mockAxios,
        preferences: mockPreferences,
      });

      expect(mockAxios.put).toHaveBeenCalledWith(
        "/api/v1/households/meals/randomizer/preferences",
        mockPreferences,
      );
      expect(store.state.mealRandomizer.userPreferences).toEqual(mockPreferences);
    });

    it("handles API errors gracefully", async () => {
      mockAxios.post.mockRejectedValue(new Error("API Error"));

      await expect(
        store.dispatch("mealRandomizer/generatePlan", {
          axios: mockAxios,
          request: {},
        }),
      ).rejects.toThrow("API Error");

      expect(store.state.mealRandomizer.loading).toBe(false);
    });
  });
});
