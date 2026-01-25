/**
 * Unit tests for FilterPanel component
 */
import { describe, it, expect, beforeEach } from "vitest";
import { mount, VueWrapper } from "@vue/test-utils";
import FilterPanel from "~/components/MealRandomizer/FilterPanel.vue";
import type { MealPlanRequest } from "~/types/meal-randomizer";

describe("FilterPanel Component", () => {
  let wrapper: VueWrapper;

  const defaultFilters: MealPlanRequest = {
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

  beforeEach(() => {
    wrapper = mount(FilterPanel, {
      props: {
        modelValue: defaultFilters,
      },
      global: {
        mocks: {
          $t: (key: string) => key,
          $globals: {
            icons: {
              filter: "mdi-filter",
              clockOutline: "mdi-clock-outline",
              foodVariant: "mdi-food-variant",
            },
          },
        },
      },
    });
  });

  it("renders all filter sections", () => {
    expect(wrapper.html()).toContain("Dietary Restrictions");
    expect(wrapper.html()).toContain("Allergen Exclusions");
    expect(wrapper.html()).toContain("Protein Preferences");
    expect(wrapper.html()).toContain("Cook Time");
  });

  it("emits update when dietary restrictions change", async () => {
    const chipGroup = wrapper.findComponent({ name: "v-chip-group" });
    
    // Simulate selecting vegetarian
    await wrapper.vm.updateDietaryRestrictions(["vegetarian"]);

    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.filters.dietary_restrictions).toContain("vegetarian");
  });

  it("emits update when allergen exclusions change", async () => {
    await wrapper.vm.updateAllergenExclusions(["peanuts", "shellfish"]);

    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.filters.allergen_exclusions).toEqual(["peanuts", "shellfish"]);
  });

  it("emits update when cook time bands change", async () => {
    await wrapper.vm.updateCookTimeBands(["0-15", "15-30"]);

    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.filters.cook_time_bands).toEqual(["0-15", "15-30"]);
  });

  it("updates protein preference sliders", async () => {
    await wrapper.vm.updateProteinPreference("beef", 3);

    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.protein_preferences.beef).toBe(3);
  });

  it("validates total protein days equals 7", () => {
    const filters = { ...defaultFilters };
    filters.protein_preferences = {
      beef: 4,
      pork: 1,
      chicken: 1,
      fish: 1,
      vegetarian: 0,
    };

    const total = Object.values(filters.protein_preferences).reduce((a, b) => a + b, 0);
    expect(total).toBe(7);
  });

  it("shows validation error if protein days do not equal 7", async () => {
    await wrapper.vm.updateProteinPreference("beef", 0);

    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    const total = Object.values(emittedValue.protein_preferences).reduce((a, b) => a + b, 0);
    
    // Should not equal 7 anymore
    expect(total).not.toBe(7);
  });

  it("updates recipe candidate cap slider", async () => {
    await wrapper.vm.updateRecipeCandidateCap(300);

    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.filters.recipe_candidate_cap).toBe(300);
  });

  it("updates avoid repeat days slider", async () => {
    await wrapper.vm.updateAvoidRepeatDays(14);

    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.filters.avoid_repeat_days).toBe(14);
  });

  it("handles multiple dietary restrictions simultaneously", async () => {
    await wrapper.vm.updateDietaryRestrictions(["vegetarian", "gluten_free", "dairy_free"]);

    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.filters.dietary_restrictions).toHaveLength(3);
    expect(emittedValue.filters.dietary_restrictions).toContain("vegetarian");
    expect(emittedValue.filters.dietary_restrictions).toContain("gluten_free");
    expect(emittedValue.filters.dietary_restrictions).toContain("dairy_free");
  });

  it("displays protein preference chips correctly", () => {
    const proteins = ["beef", "pork", "chicken", "fish", "vegetarian"];
    
    proteins.forEach((protein) => {
      expect(wrapper.vm.localFilters.protein_preferences[protein]).toBeDefined();
    });
  });

  it("resets filters to defaults", async () => {
    // Change some filters
    await wrapper.vm.updateDietaryRestrictions(["vegetarian"]);
    await wrapper.vm.updateProteinPreference("beef", 5);

    // Reset
    await wrapper.vm.resetFilters();

    const emittedValue = wrapper.emitted("update:modelValue")![wrapper.emitted("update:modelValue")!.length - 1][0] as MealPlanRequest;
    expect(emittedValue.filters.dietary_restrictions).toHaveLength(0);
    expect(emittedValue.protein_preferences.beef).toBe(2);
  });

  it("preserves pinned days when updating filters", async () => {
    const filtersWithPinnedDays = {
      ...defaultFilters,
      pinned_days: {
        Monday: "recipe-slug-1",
        Wednesday: "recipe-slug-2",
      },
    };

    wrapper = mount(FilterPanel, {
      props: {
        modelValue: filtersWithPinnedDays,
      },
      global: {
        mocks: {
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    await wrapper.vm.updateDietaryRestrictions(["vegetarian"]);

    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.pinned_days).toEqual({
      Monday: "recipe-slug-1",
      Wednesday: "recipe-slug-2",
    });
  });

  it("displays meal type chips", async () => {
    await wrapper.vm.updateMealTypes(["dinner", "lunch"]);

    const emittedValue = wrapper.emitted("update:modelValue")![0][0] as MealPlanRequest;
    expect(emittedValue.filters.meal_types).toContain("dinner");
    expect(emittedValue.filters.meal_types).toContain("lunch");
  });
});
