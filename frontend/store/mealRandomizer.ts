/**
 * Vuex Store Module for Meal Randomizer
 */

import type { RandomizerResponse, RandomizerRequest, RandomizerTemplateSummary } from "~/lib/api/types/meal-randomizer";

interface MealRandomizerState {
  isDialogOpen: boolean;
  currentResult: RandomizerResponse | null;
  savedTemplates: RandomizerTemplateSummary[];
  lastRequest: RandomizerRequest | null;
  loading: boolean;
  error: string | null;
}

export const state = (): MealRandomizerState => ({
  isDialogOpen: false,
  currentResult: null,
  savedTemplates: [],
  lastRequest: null,
  loading: false,
  error: null,
});

export const getters = {
  isOpen: (state: MealRandomizerState) => state.isDialogOpen,
  hasResult: (state: MealRandomizerState) => state.currentResult !== null,
  result: (state: MealRandomizerState) => state.currentResult,
  templates: (state: MealRandomizerState) => state.savedTemplates,
  lastRequest: (state: MealRandomizerState) => state.lastRequest,
  isLoading: (state: MealRandomizerState) => state.loading,
  error: (state: MealRandomizerState) => state.error,
};

export const mutations = {
  SET_DIALOG_OPEN(state: MealRandomizerState, value: boolean) {
    state.isDialogOpen = value;
  },

  SET_RESULT(state: MealRandomizerState, result: RandomizerResponse | null) {
    state.currentResult = result;
  },

  SET_TEMPLATES(state: MealRandomizerState, templates: RandomizerTemplateSummary[]) {
    state.savedTemplates = templates;
  },

  SET_LAST_REQUEST(state: MealRandomizerState, request: RandomizerRequest) {
    state.lastRequest = request;
  },

  SET_LOADING(state: MealRandomizerState, value: boolean) {
    state.loading = value;
  },

  SET_ERROR(state: MealRandomizerState, error: string | null) {
    state.error = error;
  },

  CLEAR_RESULT(state: MealRandomizerState) {
    state.currentResult = null;
    state.error = null;
  },
};

export const actions = {
  openDialog({ commit }: any) {
    commit("SET_DIALOG_OPEN", true);
  },

  closeDialog({ commit }: any) {
    commit("SET_DIALOG_OPEN", false);
  },

  setResult({ commit }: any, result: RandomizerResponse) {
    commit("SET_RESULT", result);
    commit("SET_ERROR", null);
  },

  setTemplates({ commit }: any, templates: RandomizerTemplateSummary[]) {
    commit("SET_TEMPLATES", templates);
  },

  setLastRequest({ commit }: any, request: RandomizerRequest) {
    commit("SET_LAST_REQUEST", request);
  },

  setLoading({ commit }: any, value: boolean) {
    commit("SET_LOADING", value);
  },

  setError({ commit }: any, error: string) {
    commit("SET_ERROR", error);
  },

  clearResult({ commit }: any) {
    commit("CLEAR_RESULT");
  },

  async generatePlan({ commit, dispatch }: any, request: RandomizerRequest) {
    const { $axios } = useNuxtApp();

    try {
      commit("SET_LOADING", true);
      commit("SET_ERROR", null);

      const { data } = await $axios.post<RandomizerResponse>(
        "/api/households/meals/randomizer/generate",
        request,
      );

      commit("SET_RESULT", data);
      commit("SET_LAST_REQUEST", request);

      return data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "Failed to generate meal plan";
      commit("SET_ERROR", errorMessage);
      throw error;
    } finally {
      commit("SET_LOADING", false);
    }
  },

  async fetchTemplates({ commit }: any) {
    const { $axios } = useNuxtApp();

    try {
      const { data } = await $axios.get<RandomizerTemplateSummary[]>(
        "/api/households/meals/randomizer/templates",
      );

      commit("SET_TEMPLATES", data || []);

      return data;
    } catch (error: any) {
      console.error("Failed to fetch templates:", error);
      return [];
    }
  },

  async saveTemplate({ dispatch }: any, { templateName, weekPlan }: any) {
    const { $axios } = useNuxtApp();

    try {
      await $axios.post("/api/households/meals/randomizer/templates", {
        template_name: templateName,
        week_plan_json: weekPlan,
      });

      // Refresh templates
      await dispatch("fetchTemplates");
    } catch (error: any) {
      console.error("Failed to save template:", error);
      throw error;
    }
  },

  async deleteTemplate({ dispatch }: any, templateId: string) {
    const { $axios } = useNuxtApp();

    try {
      await $axios.delete(`/api/households/meals/randomizer/templates/${templateId}`);

      // Refresh templates
      await dispatch("fetchTemplates");
    } catch (error: any) {
      console.error("Failed to delete template:", error);
      throw error;
    }
  },

  async rateRecipe(_: any, { recipeId, rating }: any) {
    const { $axios } = useNuxtApp();

    try {
      await $axios.post("/api/v1/households/meals/randomizer/rate", {
        recipe_id: recipeId,
        rating,
      });
    } catch (error: any) {
      console.error("Failed to rate recipe:", error);
      throw error;
    }
  },
};
