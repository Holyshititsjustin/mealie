/**
 * Unit tests for MealRandomizer Vue component
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, VueWrapper } from "@vue/test-utils";
import MealRandomizer from "~/components/MealRandomizer/MealRandomizer.vue";

describe("MealRandomizer Component", () => {
  let wrapper: VueWrapper;
  
  const mockAxios = {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders dialog when modelValue is true", () => {
    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: {
            icons: {
              close: "mdi-close",
              information: "mdi-information",
              robotHappy: "mdi-robot-happy",
              calendar: "mdi-calendar",
              cart: "mdi-cart",
              bookmark: "mdi-bookmark",
            },
          },
        },
      },
    });

    expect(wrapper.exists()).toBe(true);
  });

  it("emits update:modelValue when dialog is closed", async () => {
    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    // Simulate closing dialog
    await wrapper.vm.isOpen = false;

    expect(wrapper.emitted("update:modelValue")).toBeTruthy();
    expect(wrapper.emitted("update:modelValue")![0]).toEqual([false]);
  });

  it("initializes with default filters", () => {
    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    expect(wrapper.vm.currentFilters).toBeDefined();
    expect(wrapper.vm.currentFilters.filters.recipe_candidate_cap).toBe(200);
    expect(wrapper.vm.currentFilters.filters.avoid_repeat_days).toBe(7);
  });

  it("calls API to generate meal plan", async () => {
    const mockResponse = {
      data: {
        week_plan: [],
        shopping_consolidated: {},
        substitution_suggestions: [],
        metadata: {
          generated_at: "2026-01-24T00:00:00Z",
          generation_method: "random",
        },
        is_cached: false,
      },
    };

    mockAxios.post.mockResolvedValue(mockResponse);

    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    await wrapper.vm.generatePlan();

    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/households/meals/randomizer/generate",
      expect.any(Object),
    );

    expect(wrapper.vm.resultsReady).toBe(true);
    expect(wrapper.vm.lastResult).toEqual(mockResponse.data);
  });

  it("fetches templates on mount when dialog is open", async () => {
    const mockTemplates = [
      {
        id: "1",
        template_name: "Summer Weeknights",
        recipe_names: ["Recipe 1", "Recipe 2"],
        created_at: "2026-01-01T00:00:00Z",
      },
    ];

    mockAxios.get.mockResolvedValue({ data: mockTemplates });

    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    // Wait for onMounted hook
    await wrapper.vm.$nextTick();

    expect(mockAxios.get).toHaveBeenCalledWith(
      "/api/v1/households/meals/randomizer/templates",
    );
  });

  it("saves template successfully", async () => {
    mockAxios.post.mockResolvedValue({ data: {} });
    mockAxios.get.mockResolvedValue({ data: [] });

    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    wrapper.vm.lastResult = {
      week_plan: [
        {
          day: "Monday",
          date: "2026-01-27",
          recipe_id: "1",
          recipe_name: "Test Recipe",
          recipe_slug: "test-recipe",
          cook_time: 30,
          difficulty: "easy",
          dietary_tags: [],
          pinned: false,
        },
      ],
      shopping_consolidated: {},
      substitution_suggestions: [],
      metadata: {
        generated_at: "2026-01-24T00:00:00Z",
        generation_method: "random",
      },
      is_cached: false,
    };

    await wrapper.vm.saveAsTemplate("Test Template");

    expect(mockAxios.post).toHaveBeenCalledWith(
      "/api/v1/households/meals/randomizer/templates",
      expect.objectContaining({
        template_name: "Test Template",
      }),
    );

    // Should refresh templates
    expect(mockAxios.get).toHaveBeenCalled();
  });

  it("handles API errors gracefully", async () => {
    mockAxios.post.mockRejectedValue(new Error("API Error"));

    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    await wrapper.vm.generatePlan();

    // Should not crash and should set loading to false
    expect(wrapper.vm.loading).toBe(false);
    expect(wrapper.vm.resultsReady).toBe(false);
  });

  it("switches between tabs correctly", async () => {
    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    // Set results ready
    wrapper.vm.resultsReady = true;
    wrapper.vm.lastResult = {
      week_plan: [],
      shopping_consolidated: {},
      substitution_suggestions: [],
      metadata: {
        generated_at: "2026-01-24T00:00:00Z",
        generation_method: "random",
      },
      is_cached: false,
    };

    await wrapper.vm.$nextTick();

    // Default tab should be 0 (meal plan)
    expect(wrapper.vm.activeTab).toBe(0);

    // Switch to shopping list tab
    wrapper.vm.activeTab = 1;
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.activeTab).toBe(1);

    // Switch to templates tab
    wrapper.vm.activeTab = 2;
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.activeTab).toBe(2);
  });

  it("resets to filters view when back button clicked", async () => {
    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    // Set results ready
    wrapper.vm.resultsReady = true;
    wrapper.vm.lastResult = { week_plan: [] };

    await wrapper.vm.$nextTick();

    // Click back to filters
    wrapper.vm.backToFilters();

    expect(wrapper.vm.resultsReady).toBe(false);
    expect(wrapper.vm.activeTab).toBe(0);
  });

  it("shows loading state during generation", async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockAxios.post.mockReturnValue(promise);

    wrapper = mount(MealRandomizer, {
      props: {
        modelValue: true,
      },
      global: {
        mocks: {
          $axios: mockAxios,
          $t: (key: string) => key,
          $globals: { icons: {} },
        },
      },
    });

    // Start generation
    const generatePromise = wrapper.vm.generatePlan();

    // Should be loading
    expect(wrapper.vm.loading).toBe(true);

    // Resolve the promise
    resolvePromise!({ data: { week_plan: [], shopping_consolidated: {} } });
    await generatePromise;

    // Should no longer be loading
    expect(wrapper.vm.loading).toBe(false);
  });
});
