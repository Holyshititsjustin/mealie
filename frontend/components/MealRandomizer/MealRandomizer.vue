<template>
  <v-dialog
    v-model="isOpen"
    max-width="1200"
    persistent
    @update:model-value="onDialogClose"
  >
    <v-card>
      <v-toolbar color="primary" dark>
        <v-toolbar-title>{{ $t('meal-randomizer.title') }}</v-toolbar-title>
        <v-spacer />
        <v-btn
          icon
          @click="isOpen = false"
        >
          <v-icon>{{ $globals.icons.close }}</v-icon>
        </v-btn>
      </v-toolbar>

      <v-card-text class="pa-6">
        <v-container fluid>
          <v-row v-if="!resultsReady" gutter="4">
            <!-- Left panel: Filters -->
            <v-col cols="12" md="4">
              <FilterPanel
                v-model:filters="currentFilters"
                :loading="loading"
                @generate="generatePlan"
              />
            </v-col>

            <!-- Right panel: Help text -->
            <v-col cols="12" md="8">
              <v-alert
                type="info"
                :icon="$globals.icons.information"
                class="mb-4"
              >
                {{ $t('meal-randomizer.help-text') }}
              </v-alert>
              <v-card
                outlined
                class="pa-4 text-center"
              >
                <v-icon size="64" class="mb-4">{{ $globals.icons.robotHappy }}</v-icon>
                <p class="text-h6">
                  {{ $t('meal-randomizer.ready-to-randomize') }}
                </p>
              </v-card>
            </v-col>
          </v-row>

          <!-- Results View -->
          <v-row v-else gutter="4">
            <!-- Tabs for results, shopping list, templates -->
            <v-col cols="12">
              <v-tabs v-model="activeTab">
                <v-tab :value="0">
                  <v-icon start>{{ $globals.icons.calendar }}</v-icon>
                  {{ $t('meal-randomizer.meal-plan') }}
                </v-tab>
                <v-tab :value="1">
                  <v-icon start>{{ $globals.icons.cart }}</v-icon>
                  {{ $t('meal-randomizer.shopping-list') }}
                </v-tab>
                <v-tab :value="2">
                  <v-icon start>{{ $globals.icons.bookmark }}</v-icon>
                  {{ $t('meal-randomizer.templates') }}
                </v-tab>
              </v-tabs>
            </v-col>

            <v-col cols="12">
              <!-- Meal Plan Tab -->
              <v-window v-model="activeTab">
                <v-window-item :value="0">
                  <ResultsGrid
                    v-if="lastResult"
                    :result="lastResult"
                    @regenerate-day="regenerateDay"
                    @save-as-template="saveAsTemplate"
                  />
                </v-window-item>

                <!-- Shopping List Tab -->
                <v-window-item :value="1">
                  <ShoppingListIntegration
                    v-if="lastResult"
                    :shopping-list="lastResult.shopping_consolidated"
                    :substitutions="lastResult.substitution_suggestions"
                  />
                </v-window-item>

                <!-- Templates Tab -->
                <v-window-item :value="2">
                  <TemplateManager
                    :templates="savedTemplates"
                    @load-template="loadTemplate"
                  />
                </v-window-item>
              </v-window>
            </v-col>

            <!-- Warnings Alert -->
            <v-col v-if="lastResult?.warning_message" cols="12">
              <v-alert
                type="warning"
                :icon="$globals.icons.alertCircle"
              >
                {{ lastResult.warning_message }}
              </v-alert>
            </v-col>

            <!-- Cache Status -->
            <v-col v-if="lastResult?.is_cached" cols="12">
              <v-alert
                type="success"
                variant="tonal"
              >
                {{ $t('meal-randomizer.loaded-from-cache') }}
              </v-alert>
            </v-col>
          </v-row>

          <!-- Action Buttons -->
          <v-row class="mt-4" gutter="2">
            <v-col cols="auto">
              <v-btn
                v-if="resultsReady"
                variant="outlined"
                @click="backToFilters"
              >
                {{ $t('common.back') }}
              </v-btn>
            </v-col>
            <v-col v-if="resultsReady" cols="auto">
              <v-btn
                variant="outlined"
                @click="regeneratePlan"
                :loading="loading"
              >
                {{ $t('meal-randomizer.regenerate') }}
              </v-btn>
            </v-col>
            <v-col v-if="resultsReady" cols="auto" class="ml-auto">
              <v-btn
                color="primary"
                @click="applyToMealPlan"
                :loading="savingToPlan"
              >
                {{ $t('meal-randomizer.apply-to-meal-plan') }}
              </v-btn>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import { defineNuxtComponent } from "#app";
import { format, isWithinInterval, parseISO } from "date-fns";
import type { PropType } from "vue";
import type { MealsByDate } from "~/pages/household/mealplan/planner/types";
import { useUserApi } from "~/composables/api";
import type { RandomizerResponse, RandomizerRequest } from "~/lib/api/types/meal-randomizer";

export default defineNuxtComponent({
  components: {
    FilterPanel: () => import("./FilterPanel.vue"),
    ResultsGrid: () => import("./ResultsGrid.vue"),
    ShoppingListIntegration: () => import("./ShoppingListIntegration.vue"),
    TemplateManager: () => import("./TemplateManager.vue"),
  },
  emits: ["update:modelValue", "applied"],
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    startDate: {
      type: Date,
      required: true,
    },
    endDate: {
      type: Date,
      required: true,
    },
    mealsByDate: {
      type: Array as PropType<MealsByDate[]>,
      default: () => [],
    },
  },
  setup(props, { emit }) {
    const { $axios } = useNuxtApp();
    const api = useUserApi();
    const isOpen = computed({
      get: () => props.modelValue,
      set: (value) => emit("update:modelValue", value),
    });

    const loading = ref(false);
    const savingToPlan = ref(false);
    const resultsReady = ref(false);
    const activeTab = ref(0);

    const currentFilters = ref<RandomizerRequest>({
      start_date: format(props.startDate ?? new Date(), "yyyy-MM-dd"),
      filters: {
        dietary_restrictions: [],
        allergens: [],
        protein_preferences: [],
        avoid_repeat_days: 7,
        cook_time_bands: [],
        meal_types: [],
        difficulty_levels: [],
        include_expiring_ingredients: false,
        recipe_candidate_cap: 200,
      },
      pinned_days: {},
    });

    const lastResult = ref<RandomizerResponse | null>(null);
    const savedTemplates = ref<any[]>([]);

    const blockedDates = computed(() => {
      const occupied = new Set<string>();
      props.mealsByDate.forEach((day) => {
        if (day.meals && day.meals.length > 0) {
          occupied.add(format(day.date, "yyyy-MM-dd"));
        }
      });
      return occupied;
    });

    const withinPlannerRange = (dateStr: string) => {
      const date = parseISO(dateStr);
      if (Number.isNaN(date.getTime())) {
        return false;
      }
      return isWithinInterval(date, { start: props.startDate, end: props.endDate });
    };

    watch(
      () => props.startDate,
      (value) => {
        if (value) {
          currentFilters.value.start_date = format(value, "yyyy-MM-dd");
        }
      },
      { immediate: true },
    );

    // Fetch saved templates
    const fetchTemplates = async () => {
      try {
        const { data } = await $axios.get("/api/households/meals/randomizer/templates");
        savedTemplates.value = data || [];
      } catch (error) {
        console.error("Error fetching templates:", error);
      }
    };

    // Generate meal plan
    const generatePlan = async () => {
      loading.value = true;
      try {
        const { data } = await $axios.post<RandomizerResponse>(
          "/api/households/meals/randomizer/generate",
          currentFilters.value,
        );
        lastResult.value = data;
        resultsReady.value = true;
        activeTab.value = 0;
      } catch (error) {
        console.error("Error generating plan:", error);
        // TODO: Show error toast
      } finally {
        loading.value = false;
      }
    };

    // Regenerate entire plan
    const regeneratePlan = async () => {
      loading.value = true;
      try {
        const { data } = await $axios.post<RandomizerResponse>(
          "/api/households/meals/randomizer/generate",
          currentFilters.value,
        );
        lastResult.value = data;
      } catch (error) {
        console.error("Error regenerating plan:", error);
      } finally {
        loading.value = false;
      }
    };

    // Regenerate single day
    const regenerateDay = async (dayIndex: number) => {
      // TODO: Implement per-day regeneration if API supports it
      console.log("Regenerate day:", dayIndex);
    };

    // Save current result as template
    const saveAsTemplate = async (templateName: string) => {
      if (!lastResult.value) return;

      try {
        await $axios.post("/api/households/meals/randomizer/templates", {
          template_name: templateName,
          week_plan_json: lastResult.value.week_plan,
        });
        await fetchTemplates();
        // TODO: Show success toast
      } catch (error) {
        console.error("Error saving template:", error);
      }
    };

    // Load template
    const loadTemplate = async (templateId: string) => {
      try {
        const { data } = await $axios.get(
          `/api/households/meals/randomizer/templates/${templateId}`,
        );
        // TODO: Parse week_plan_json and apply to meal plan
        console.log("Load template:", data);
      } catch (error) {
        console.error("Error loading template:", error);
      }
    };

    // Apply to meal plan
    const applyToMealPlan = async () => {
      if (!lastResult.value) return;

      savingToPlan.value = true;
      try {
        const entries = lastResult.value.week_plan
          .filter((card) => withinPlannerRange(card.date))
          .map((card) => ({
            normalizedDate: format(parseISO(card.date), "yyyy-MM-dd"),
            card,
          }))
          .filter(({ normalizedDate }) => !blockedDates.value.has(normalizedDate));

        if (entries.length === 0) {
          isOpen.value = false;
          emit("applied");
          return;
        }

        await Promise.all(
          entries.map(({ normalizedDate, card }) =>
            api.mealplans.createOne({
              date: normalizedDate,
              entryType: "dinner",
              recipeId: card.recipe_id,
              title: card.recipe_name,
            }),
          ),
        );

        emit("applied");
        isOpen.value = false;
      } catch (error) {
        console.error("Error applying to meal plan:", error);
      } finally {
        savingToPlan.value = false;
      }
    };

    // Back to filters
    const backToFilters = () => {
      resultsReady.value = false;
      activeTab.value = 0;
    };

    const onDialogClose = (value: boolean) => {
      if (!value) {
        backToFilters();
      }
    };

    onMounted(() => {
      if (isOpen.value) {
        fetchTemplates();
      }
    });

    watch(isOpen, (value) => {
      if (value) {
        fetchTemplates();
      }
    });

    return {
      isOpen,
      loading,
      savingToPlan,
      resultsReady,
      activeTab,
      currentFilters,
      lastResult,
      savedTemplates,
      generatePlan,
      regeneratePlan,
      regenerateDay,
      saveAsTemplate,
      loadTemplate,
      applyToMealPlan,
      backToFilters,
      onDialogClose,
    };
  },
});
</script>

<style scoped>
/* Component styling */
</style>
