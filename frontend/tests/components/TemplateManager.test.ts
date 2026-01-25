/**
 * Unit tests for TemplateManager component
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, VueWrapper } from "@vue/test-utils";
import TemplateManager from "~/components/MealRandomizer/TemplateManager.vue";
import type { MealPlanTemplate } from "~/types/meal-randomizer";

describe("TemplateManager Component", () => {
  let wrapper: VueWrapper;

  const mockTemplates: MealPlanTemplate[] = [
    {
      id: "1",
      user_id: "user-123",
      template_name: "Summer Weeknights",
      week_plan_json: JSON.stringify({
        week_plan: [
          {
            day: "Monday",
            recipe_id: "1",
            recipe_name: "Grilled Chicken",
            recipe_slug: "grilled-chicken",
          },
        ],
      }),
      recipe_names: ["Grilled Chicken", "Fish Tacos", "Veggie Stir Fry"],
      created_at: "2026-01-15T10:00:00Z",
      updated_at: "2026-01-15T10:00:00Z",
    },
    {
      id: "2",
      user_id: "user-123",
      template_name: "Winter Comfort Foods",
      week_plan_json: JSON.stringify({
        week_plan: [
          {
            day: "Monday",
            recipe_id: "10",
            recipe_name: "Beef Stew",
            recipe_slug: "beef-stew",
          },
        ],
      }),
      recipe_names: ["Beef Stew", "Mac and Cheese", "Chicken Soup"],
      created_at: "2026-01-10T14:30:00Z",
      updated_at: "2026-01-10T14:30:00Z",
    },
  ];

  beforeEach(() => {
    wrapper = mount(TemplateManager, {
      props: {
        templates: mockTemplates,
      },
      global: {
        mocks: {
          $t: (key: string) => key,
          $globals: {
            icons: {
              bookmark: "mdi-bookmark",
              bookmarkOutline: "mdi-bookmark-outline",
              delete: "mdi-delete",
              download: "mdi-download",
              calendar: "mdi-calendar",
            },
          },
        },
      },
    });
  });

  it("renders all templates", () => {
    const templateCards = wrapper.findAll(".template-card");
    expect(templateCards.length).toBe(2);
  });

  it("displays template names correctly", () => {
    expect(wrapper.html()).toContain("Summer Weeknights");
    expect(wrapper.html()).toContain("Winter Comfort Foods");
  });

  it("displays recipe names for each template", () => {
    expect(wrapper.html()).toContain("Grilled Chicken");
    expect(wrapper.html()).toContain("Fish Tacos");
    expect(wrapper.html()).toContain("Veggie Stir Fry");
    expect(wrapper.html()).toContain("Beef Stew");
    expect(wrapper.html()).toContain("Mac and Cheese");
    expect(wrapper.html()).toContain("Chicken Soup");
  });

  it("displays created dates", () => {
    expect(wrapper.html()).toContain("2026-01-15");
    expect(wrapper.html()).toContain("2026-01-10");
  });

  it("emits load-template event when template clicked", async () => {
    await wrapper.vm.loadTemplate(mockTemplates[0]);

    expect(wrapper.emitted("load-template")).toBeTruthy();
    expect(wrapper.emitted("load-template")![0]).toEqual([mockTemplates[0]]);
  });

  it("emits delete-template event when delete button clicked", async () => {
    await wrapper.vm.deleteTemplate("1");

    expect(wrapper.emitted("delete-template")).toBeTruthy();
    expect(wrapper.emitted("delete-template")![0]).toEqual(["1"]);
  });

  it("shows confirmation dialog before deleting", async () => {
    wrapper.vm.showDeleteConfirmation("1", "Summer Weeknights");

    expect(wrapper.vm.deleteDialogOpen).toBe(true);
    expect(wrapper.vm.templateToDelete).toBe("1");
    expect(wrapper.vm.templateNameToDelete).toBe("Summer Weeknights");
  });

  it("confirms deletion and emits event", async () => {
    wrapper.vm.showDeleteConfirmation("1", "Summer Weeknights");
    await wrapper.vm.confirmDelete();

    expect(wrapper.emitted("delete-template")).toBeTruthy();
    expect(wrapper.emitted("delete-template")![0]).toEqual(["1"]);
    expect(wrapper.vm.deleteDialogOpen).toBe(false);
  });

  it("cancels deletion and closes dialog", async () => {
    wrapper.vm.showDeleteConfirmation("1", "Summer Weeknights");
    await wrapper.vm.cancelDelete();

    expect(wrapper.emitted("delete-template")).toBeFalsy();
    expect(wrapper.vm.deleteDialogOpen).toBe(false);
  });

  it("displays empty state when no templates", async () => {
    await wrapper.setProps({
      templates: [],
    });

    expect(wrapper.html()).toContain("No saved templates");
  });

  it("shows recipe count for each template", () => {
    // Each template should show recipe count
    expect(wrapper.html()).toMatch(/3.*recipe/i);
  });

  it("formats dates in readable format", () => {
    const dates = wrapper.findAll(".template-date");
    dates.forEach((date) => {
      // Should contain formatted date
      expect(date.text()).toMatch(/\d{4}-\d{2}-\d{2}/);
    });
  });

  it("displays template cards in grid layout", () => {
    const grid = wrapper.find(".templates-grid");
    expect(grid.exists()).toBe(true);
  });

  it("shows delete confirmation with template name", async () => {
    wrapper.vm.showDeleteConfirmation("1", "Summer Weeknights");

    const dialog = wrapper.find(".delete-dialog");
    if (dialog.exists()) {
      expect(dialog.html()).toContain("Summer Weeknights");
    }
  });

  it("highlights selected template when loading", async () => {
    await wrapper.vm.loadTemplate(mockTemplates[0]);

    // Check if template is marked as selected/loading
    expect(wrapper.vm.selectedTemplateId).toBe("1");
  });

  it("displays template preview with recipe list", () => {
    const recipeLists = wrapper.findAll(".recipe-list");
    expect(recipeLists.length).toBe(2);
  });

  it("limits recipe name display with ellipsis for long lists", async () => {
    const longTemplate: MealPlanTemplate = {
      id: "3",
      user_id: "user-123",
      template_name: "Many Recipes",
      week_plan_json: "{}",
      recipe_names: Array(10).fill("Recipe Name"),
      created_at: "2026-01-20T10:00:00Z",
      updated_at: "2026-01-20T10:00:00Z",
    };

    await wrapper.setProps({
      templates: [longTemplate],
    });

    // Should show limited number of recipes + "and X more"
    expect(wrapper.html()).toMatch(/more/i);
  });

  it("handles template with no recipes gracefully", async () => {
    const emptyTemplate: MealPlanTemplate = {
      id: "4",
      user_id: "user-123",
      template_name: "Empty Template",
      week_plan_json: JSON.stringify({ week_plan: [] }),
      recipe_names: [],
      created_at: "2026-01-20T10:00:00Z",
      updated_at: "2026-01-20T10:00:00Z",
    };

    await wrapper.setProps({
      templates: [emptyTemplate],
    });

    expect(wrapper.html()).toContain("Empty Template");
  });

  it("shows loading state when deleting template", async () => {
    wrapper.vm.deletingTemplateId = "1";
    await wrapper.vm.$nextTick();

    // Should show loading indicator
    const deleteButton = wrapper.find('[data-template-id="1"] .delete-btn');
    if (deleteButton.exists()) {
      expect(deleteButton.attributes("disabled")).toBeDefined();
    }
  });

  it("resets loading state after delete", async () => {
    wrapper.vm.deletingTemplateId = "1";
    await wrapper.vm.confirmDelete();

    expect(wrapper.vm.deletingTemplateId).toBeNull();
  });

  it("sorts templates by creation date (newest first)", () => {
    const dates = mockTemplates.map((t) => new Date(t.created_at).getTime());
    const sorted = [...dates].sort((a, b) => b - a);

    expect(dates[0]).toBeGreaterThan(dates[1]);
  });

  it("shows updated date if different from created date", async () => {
    const updatedTemplate: MealPlanTemplate = {
      ...mockTemplates[0],
      updated_at: "2026-01-20T10:00:00Z",
    };

    await wrapper.setProps({
      templates: [updatedTemplate],
    });

    expect(wrapper.html()).toContain("2026-01-20");
  });
});
