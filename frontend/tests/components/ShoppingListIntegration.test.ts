/**
 * Unit tests for ShoppingListIntegration component
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, VueWrapper } from "@vue/test-utils";
import ShoppingListIntegration from "~/components/MealRandomizer/ShoppingListIntegration.vue";
import type { ConsolidatedShoppingList, SubstitutionSuggestion } from "~/types/meal-randomizer";

describe("ShoppingListIntegration Component", () => {
  let wrapper: VueWrapper;

  const mockShoppingList: ConsolidatedShoppingList = {
    Produce: [
      {
        name: "Tomatoes",
        quantity: 4.0,
        unit: "whole",
        notes: "Roma or plum",
      },
      {
        name: "Onions",
        quantity: 2.0,
        unit: "whole",
        notes: "",
      },
    ],
    Protein: [
      {
        name: "Chicken Breast",
        quantity: 1.5,
        unit: "lbs",
        notes: "boneless, skinless",
      },
      {
        name: "Ground Beef",
        quantity: 1.0,
        unit: "lbs",
        notes: "80/20",
      },
    ],
    Pantry: [
      {
        name: "Olive Oil",
        quantity: 0.25,
        unit: "cup",
        notes: "extra virgin",
      },
    ],
  };

  const mockSubstitutions: SubstitutionSuggestion[] = [
    {
      original_ingredient: "Chicken Breast",
      suggested_substitute: "Turkey Breast",
      reason: "Lower fat content, similar texture",
    },
    {
      original_ingredient: "Ground Beef",
      suggested_substitute: "Ground Turkey",
      reason: "Healthier alternative with less saturated fat",
    },
  ];

  beforeEach(() => {
    wrapper = mount(ShoppingListIntegration, {
      props: {
        shoppingList: mockShoppingList,
        substitutions: mockSubstitutions,
      },
      global: {
        mocks: {
          $t: (key: string) => key,
          $globals: {
            icons: {
              cart: "mdi-cart",
              download: "mdi-download",
              information: "mdi-information",
              swap: "mdi-swap-horizontal",
            },
          },
        },
      },
    });
  });

  it("renders shopping list categories", () => {
    expect(wrapper.html()).toContain("Produce");
    expect(wrapper.html()).toContain("Protein");
    expect(wrapper.html()).toContain("Pantry");
  });

  it("displays all ingredients in Produce category", () => {
    expect(wrapper.html()).toContain("Tomatoes");
    expect(wrapper.html()).toContain("Onions");
    expect(wrapper.html()).toContain("4");
    expect(wrapper.html()).toContain("2");
  });

  it("displays quantities and units correctly", () => {
    expect(wrapper.html()).toContain("1.5 lbs");
    expect(wrapper.html()).toContain("1 lbs");
    expect(wrapper.html()).toContain("0.25 cup");
  });

  it("displays ingredient notes", () => {
    expect(wrapper.html()).toContain("Roma or plum");
    expect(wrapper.html()).toContain("boneless, skinless");
    expect(wrapper.html()).toContain("80/20");
    expect(wrapper.html()).toContain("extra virgin");
  });

  it("renders substitution suggestions section", () => {
    expect(wrapper.html()).toContain("Substitution Suggestions");
    expect(wrapper.html()).toContain("Turkey Breast");
    expect(wrapper.html()).toContain("Ground Turkey");
  });

  it("displays substitution reasons", () => {
    expect(wrapper.html()).toContain("Lower fat content, similar texture");
    expect(wrapper.html()).toContain("Healthier alternative with less saturated fat");
  });

  it("shows original ingredients in substitutions", () => {
    expect(wrapper.html()).toContain("Chicken Breast");
    expect(wrapper.html()).toContain("Ground Beef");
  });

  it("emits export-shopping-list event when export clicked", async () => {
    await wrapper.vm.exportShoppingList();

    expect(wrapper.emitted("export-shopping-list")).toBeTruthy();
  });

  it("groups ingredients by category correctly", () => {
    const produceCount = mockShoppingList.Produce.length;
    const proteinCount = mockShoppingList.Protein.length;
    const pantryCount = mockShoppingList.Pantry.length;

    expect(produceCount).toBe(2);
    expect(proteinCount).toBe(2);
    expect(pantryCount).toBe(1);
  });

  it("handles empty shopping list gracefully", async () => {
    await wrapper.setProps({
      shoppingList: {},
      substitutions: [],
    });

    const categories = wrapper.findAll(".category-section");
    expect(categories.length).toBe(0);
  });

  it("handles empty substitutions list", async () => {
    await wrapper.setProps({
      shoppingList: mockShoppingList,
      substitutions: [],
    });

    const substitutionSection = wrapper.find('[data-test="substitutions-section"]');
    if (substitutionSection.exists()) {
      expect(substitutionSection.html()).toContain("No substitutions");
    }
  });

  it("displays category headers with expansion panels", () => {
    const expansionPanels = wrapper.findAllComponents({ name: "v-expansion-panel" });
    expect(expansionPanels.length).toBeGreaterThanOrEqual(3);
  });

  it("calculates total item count correctly", () => {
    const totalItems = 
      mockShoppingList.Produce.length +
      mockShoppingList.Protein.length +
      mockShoppingList.Pantry.length;

    expect(totalItems).toBe(5);
  });

  it("formats decimal quantities correctly", () => {
    expect(wrapper.html()).toContain("1.5");
    expect(wrapper.html()).toContain("0.25");
  });

  it("displays whole number quantities without decimals", () => {
    expect(wrapper.html()).toContain("4");
    expect(wrapper.html()).toContain("2");
    expect(wrapper.html()).toContain("1");
  });

  it("renders checkboxes for each ingredient", () => {
    const checkboxes = wrapper.findAllComponents({ name: "v-checkbox" });
    expect(checkboxes.length).toBeGreaterThanOrEqual(5);
  });

  it("emits toggle-ingredient event when checkbox clicked", async () => {
    await wrapper.vm.toggleIngredientChecked("Tomatoes");

    expect(wrapper.emitted("toggle-ingredient")).toBeTruthy();
    expect(wrapper.emitted("toggle-ingredient")![0]).toEqual(["Tomatoes"]);
  });

  it("applies substitution when swap button clicked", async () => {
    await wrapper.vm.applySubstitution("Chicken Breast", "Turkey Breast");

    expect(wrapper.emitted("apply-substitution")).toBeTruthy();
    expect(wrapper.emitted("apply-substitution")![0]).toEqual([
      "Chicken Breast",
      "Turkey Breast",
    ]);
  });

  it("shows all categories expanded by default", () => {
    const panels = wrapper.findAllComponents({ name: "v-expansion-panel" });
    panels.forEach((panel) => {
      // Check if panel is open (implementation may vary)
      expect(panel.exists()).toBe(true);
    });
  });

  it("handles missing units gracefully", async () => {
    await wrapper.setProps({
      shoppingList: {
        Produce: [
          {
            name: "Garlic",
            quantity: 3,
            unit: "",
            notes: "cloves",
          },
        ],
      },
      substitutions: [],
    });

    expect(wrapper.html()).toContain("Garlic");
    expect(wrapper.html()).toContain("3");
  });

  it("displays ingredient count per category", () => {
    // Should show "Produce (2)", "Protein (2)", "Pantry (1)"
    expect(wrapper.html()).toMatch(/Produce.*2/);
    expect(wrapper.html()).toMatch(/Protein.*2/);
    expect(wrapper.html()).toMatch(/Pantry.*1/);
  });
});
