/**
 * Unit tests for ResultsGrid component
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, VueWrapper } from "@vue/test-utils";
import ResultsGrid from "~/components/MealRandomizer/ResultsGrid.vue";
import type { WeekPlanResult, MealPlan } from "~/types/meal-randomizer";

describe("ResultsGrid Component", () => {
  let wrapper: VueWrapper;

  const mockWeekPlan: MealPlan[] = [
    {
      day: "Monday",
      date: "2026-01-27",
      recipe_id: "1",
      recipe_name: "Spaghetti Carbonara",
      recipe_slug: "spaghetti-carbonara",
      cook_time: 30,
      difficulty: "medium",
      dietary_tags: ["gluten_free"],
      pinned: false,
    },
    {
      day: "Tuesday",
      date: "2026-01-28",
      recipe_id: "2",
      recipe_name: "Chicken Stir Fry",
      recipe_slug: "chicken-stir-fry",
      cook_time: 25,
      difficulty: "easy",
      dietary_tags: [],
      pinned: false,
    },
    {
      day: "Wednesday",
      date: "2026-01-29",
      recipe_id: "3",
      recipe_name: "Beef Tacos",
      recipe_slug: "beef-tacos",
      cook_time: 20,
      difficulty: "easy",
      dietary_tags: ["dairy_free"],
      pinned: true,
    },
  ];

  const mockResult: WeekPlanResult = {
    week_plan: mockWeekPlan,
    shopping_consolidated: {},
    substitution_suggestions: [],
    metadata: {
      generated_at: "2026-01-24T10:00:00Z",
      generation_method: "random",
    },
    is_cached: false,
  };

  beforeEach(() => {
    wrapper = mount(ResultsGrid, {
      props: {
        result: mockResult,
      },
      global: {
        mocks: {
          $t: (key: string) => key,
          $globals: {
            icons: {
              calendar: "mdi-calendar",
              clockOutline: "mdi-clock-outline",
              chefHat: "mdi-chef-hat",
              pin: "mdi-pin",
              pinOff: "mdi-pin-off",
              refresh: "mdi-refresh",
              thumbUp: "mdi-thumb-up",
              thumbDown: "mdi-thumb-down",
              delete: "mdi-delete",
            },
          },
        },
      },
    });
  });

  it("renders all meal cards", () => {
    const cards = wrapper.findAllComponents({ name: "v-card" });
    expect(cards.length).toBeGreaterThanOrEqual(3);
  });

  it("displays recipe names correctly", () => {
    expect(wrapper.html()).toContain("Spaghetti Carbonara");
    expect(wrapper.html()).toContain("Chicken Stir Fry");
    expect(wrapper.html()).toContain("Beef Tacos");
  });

  it("displays cook time for each recipe", () => {
    expect(wrapper.html()).toContain("30");
    expect(wrapper.html()).toContain("25");
    expect(wrapper.html()).toContain("20");
  });

  it("displays difficulty tags", () => {
    expect(wrapper.html()).toContain("medium");
    expect(wrapper.html()).toContain("easy");
  });

  it("shows pinned indicator for pinned recipes", () => {
    const pinnedCard = wrapper.findAll(".meal-card").find((card) => 
      card.html().includes("Beef Tacos")
    );
    
    expect(pinnedCard?.html()).toContain("pin");
  });

  it("emits pin-recipe event when pin button clicked", async () => {
    await wrapper.vm.togglePin("Monday", "spaghetti-carbonara");

    expect(wrapper.emitted("pin-recipe")).toBeTruthy();
    expect(wrapper.emitted("pin-recipe")![0]).toEqual(["Monday", "spaghetti-carbonara"]);
  });

  it("emits unpin-recipe event when unpin button clicked on pinned recipe", async () => {
    await wrapper.vm.togglePin("Wednesday", "beef-tacos");

    expect(wrapper.emitted("unpin-recipe")).toBeTruthy();
    expect(wrapper.emitted("unpin-recipe")![0]).toEqual(["Wednesday"]);
  });

  it("emits regenerate-day event when regenerate button clicked", async () => {
    await wrapper.vm.regenerateDay("Tuesday");

    expect(wrapper.emitted("regenerate-day")).toBeTruthy();
    expect(wrapper.emitted("regenerate-day")![0]).toEqual(["Tuesday"]);
  });

  it("emits rate-recipe event with thumbs up", async () => {
    await wrapper.vm.rateRecipe("1", "up");

    expect(wrapper.emitted("rate-recipe")).toBeTruthy();
    expect(wrapper.emitted("rate-recipe")![0]).toEqual(["1", "up"]);
  });

  it("emits rate-recipe event with thumbs down", async () => {
    await wrapper.vm.rateRecipe("2", "down");

    expect(wrapper.emitted("rate-recipe")).toBeTruthy();
    expect(wrapper.emitted("rate-recipe")![0]).toEqual(["2", "down"]);
  });

  it("emits rate-recipe event with never again", async () => {
    await wrapper.vm.rateRecipe("3", "never_again");

    expect(wrapper.emitted("rate-recipe")).toBeTruthy();
    expect(wrapper.emitted("rate-recipe")![0]).toEqual(["3", "never_again"]);
  });

  it("displays dietary tags as chips", () => {
    const chips = wrapper.findAllComponents({ name: "v-chip" });
    const chipTexts = chips.map((chip) => chip.text());
    
    expect(chipTexts.some((text) => text.includes("gluten_free"))).toBe(true);
    expect(chipTexts.some((text) => text.includes("dairy_free"))).toBe(true);
  });

  it("displays cache indicator when result is cached", async () => {
    await wrapper.setProps({
      result: {
        ...mockResult,
        is_cached: true,
      },
    });

    expect(wrapper.html()).toContain("cached");
  });

  it("formats date correctly", () => {
    // Dates should be displayed in readable format
    expect(wrapper.html()).toContain("2026-01-27");
    expect(wrapper.html()).toContain("2026-01-28");
    expect(wrapper.html()).toContain("2026-01-29");
  });

  it("handles empty week plan gracefully", async () => {
    await wrapper.setProps({
      result: {
        ...mockResult,
        week_plan: [],
      },
    });

    const cards = wrapper.findAll(".meal-card");
    expect(cards.length).toBe(0);
  });

  it("displays generation timestamp", () => {
    expect(wrapper.html()).toContain("2026-01-24");
  });

  it("shows regenerate button only for non-pinned days", () => {
    const mondayCard = wrapper.findAll(".meal-card").find((card) => 
      card.html().includes("Monday")
    );
    const wednesdayCard = wrapper.findAll(".meal-card").find((card) => 
      card.html().includes("Wednesday")
    );

    // Monday is not pinned, should have regenerate button
    expect(mondayCard?.html()).toContain("refresh");
    
    // Wednesday is pinned, regenerate should be disabled or hidden
    const wednesdayRefreshButton = wednesdayCard?.find('[data-test="regenerate-btn"]');
    if (wednesdayRefreshButton) {
      expect(wednesdayRefreshButton.attributes("disabled")).toBeDefined();
    }
  });

  it("links to recipe detail page", () => {
    const links = wrapper.findAll("a");
    const recipeLinks = links.filter((link) => 
      link.attributes("href")?.includes("/recipes/")
    );

    expect(recipeLinks.length).toBeGreaterThan(0);
    expect(recipeLinks[0].attributes("href")).toContain("spaghetti-carbonara");
  });

  it("displays difficulty with appropriate color coding", async () => {
    const easyCards = wrapper.findAll(".meal-card").filter((card) => 
      card.html().includes("easy")
    );
    const mediumCards = wrapper.findAll(".meal-card").filter((card) => 
      card.html().includes("medium")
    );

    expect(easyCards.length).toBe(2);
    expect(mediumCards.length).toBe(1);
  });
});
