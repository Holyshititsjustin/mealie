<template>
  <v-card outlined>
    <v-card-title>{{ $t('meal-randomizer.filters') }}</v-card-title>
    <v-divider />
    <v-card-text class="pa-6">
      <v-form>
        <!-- Start Date -->
        <v-text-field
          v-model="localFilters.start_date"
          type="date"
          :label="$t('meal-randomizer.start-date')"
          class="mb-4"
          outlined
        />

        <!-- Dietary Restrictions -->
        <div class="mb-6">
          <v-label class="mb-2">{{ $t('meal-randomizer.dietary-restrictions') }}</v-label>
          <v-chip-group
            v-model="localFilters.filters.dietary_restrictions"
            multiple
            column
          >
            <v-chip
              v-for="restriction in dietaryOptions"
              :key="restriction"
              filter
              outlined
            >
              {{ restriction }}
            </v-chip>
          </v-chip-group>
        </div>

        <!-- Allergens -->
        <div class="mb-6">
          <v-label class="mb-2">{{ $t('meal-randomizer.allergens') }}</v-label>
          <v-chip-group
            v-model="localFilters.filters.allergens"
            multiple
            column
          >
            <v-chip
              v-for="allergen in allergenOptions"
              :key="allergen"
              filter
              outlined
            >
              {{ allergen }}
            </v-chip>
          </v-chip-group>
        </div>

        <!-- Protein Preferences -->
        <div class="mb-6">
          <v-label class="mb-2">{{ $t('meal-randomizer.protein-preferences') }}</v-label>
          <v-row gutter="2" class="mb-2">
            <v-col v-for="(pref, idx) in localFilters.filters.protein_preferences" :key="idx" cols="6" md="12">
              <div class="d-flex gap-2">
                <v-text-field
                  v-model="pref.protein_type"
                  label="Protein type"
                  dense
                  outlined
                  size="small"
                />
                <v-number-input
                  v-model="pref.count"
                  label="Count"
                  min="0"
                  max="7"
                  dense
                  outlined
                  size="small"
                />
                <v-btn
                  icon
                  size="small"
                  @click="removeProtein(idx)"
                >
                  <v-icon size="small">{{ $globals.icons.delete }}</v-icon>
                </v-btn>
              </div>
            </v-col>
          </v-row>
          <v-btn
            size="small"
            variant="outlined"
            prepend-icon="$plus"
            @click="addProtein"
          >
            {{ $t('common.add') }}
          </v-btn>
        </div>

        <!-- Cook Time Bands -->
        <div class="mb-6">
          <v-label class="mb-2">{{ $t('meal-randomizer.cook-time') }}</v-label>
          <v-chip-group
            v-model="localFilters.filters.cook_time_bands"
            multiple
            column
          >
            <v-chip
              v-for="time in cookTimeOptions"
              :key="time"
              filter
              outlined
            >
              {{ time }}
            </v-chip>
          </v-chip-group>
        </div>

        <!-- Meal Types -->
        <div class="mb-6">
          <v-label class="mb-2">{{ $t('meal-randomizer.meal-types') }}</v-label>
          <v-chip-group
            v-model="localFilters.filters.meal_types"
            multiple
            column
          >
            <v-chip
              v-for="type in mealTypeOptions"
              :key="type"
              filter
              outlined
            >
              {{ type }}
            </v-chip>
          </v-chip-group>
        </div>

        <!-- Difficulty Levels -->
        <div class="mb-6">
          <v-label class="mb-2">{{ $t('meal-randomizer.difficulty') }}</v-label>
          <v-chip-group
            v-model="localFilters.filters.difficulty_levels"
            multiple
            column
          >
            <v-chip
              v-for="level in difficultyOptions"
              :key="level"
              filter
              outlined
            >
              {{ level }}
            </v-chip>
          </v-chip-group>
        </div>

        <!-- Avoid Repeat Days -->
        <v-slider
          v-model="localFilters.filters.avoid_repeat_days"
          :label="`${$t('meal-randomizer.avoid-repeat-days')}: ${localFilters.filters.avoid_repeat_days}`"
          min="1"
          max="30"
          class="mb-6"
        />

        <!-- Recipe Candidate Cap -->
        <v-slider
          v-model="localFilters.filters.recipe_candidate_cap"
          :label="`${$t('meal-randomizer.recipe-candidate-cap')}: ${localFilters.filters.recipe_candidate_cap}`"
          min="10"
          max="500"
          step="10"
          class="mb-6"
        />

        <!-- Include Expiring Ingredients -->
        <v-checkbox
          v-model="localFilters.filters.include_expiring_ingredients"
          :label="$t('meal-randomizer.include-expiring-ingredients')"
          class="mb-6"
        />

        <!-- Action Buttons -->
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            block
            @click="$emit('generate')"
            :loading="loading"
          >
            {{ $t('meal-randomizer.generate') }}
          </v-btn>
        </div>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { defineNuxtComponent } from "#app";
import type { RandomizerFilters } from "~/lib/api/types/meal-randomizer";

export default defineNuxtComponent({
  emits: ["update:filters", "generate"],
  props: {
    filters: {
      type: Object as PropType<RandomizerFilters>,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
  setup(props, { emit }) {
    const dietaryOptions = [
      "Vegetarian",
      "Vegan",
      "Gluten Free",
      "Keto",
      "Paleo",
      "Dairy Free",
    ];

    const allergenOptions = [
      "Nuts",
      "Peanuts",
      "Shellfish",
      "Fish",
      "Dairy",
      "Eggs",
      "Soy",
      "Sesame",
    ];

    const cookTimeOptions = ["0-15 min", "15-30 min", "30-60 min", "60+ min"];

    const mealTypeOptions = [
      "Quick Weeknight",
      "Slow Cooker",
      "One Pot",
      "Fancy",
    ];

    const difficultyOptions = ["Easy", "Medium", "Complex"];

    const localFilters = computed({
      get: () => props.filters,
      set: (value) => emit("update:filters", value),
    });

    const addProtein = () => {
      localFilters.value.filters.protein_preferences.push({
        protein_type: "",
        count: 1,
      });
    };

    const removeProtein = (index: number) => {
      localFilters.value.filters.protein_preferences.splice(index, 1);
    };

    return {
      localFilters,
      dietaryOptions,
      allergenOptions,
      cookTimeOptions,
      mealTypeOptions,
      difficultyOptions,
      addProtein,
      removeProtein,
    };
  },
});
</script>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}
</style>
