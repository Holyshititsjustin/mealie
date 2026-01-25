<template>
  <v-container fluid>
    <v-row gutter="4">
      <!-- 7-day meal cards -->
      <v-col
        v-for="(meal, idx) in result.week_plan"
        :key="idx"
        cols="12"
        sm="6"
        lg="4"
      >
        <v-card
          :key="`meal-${idx}`"
          outlined
          class="h-100 d-flex flex-column"
        >
          <!-- Recipe Image -->
          <v-img
            v-if="meal.image_url"
            :src="meal.image_url"
            height="200"
            cover
            class="bg-grey-lighten-2"
          />
          <v-img
            v-else
            height="200"
            class="bg-grey-lighten-2 d-flex align-center justify-center"
          >
            <v-icon size="64">{{ $globals.icons.image }}</v-icon>
          </v-img>

          <v-card-title class="text-subtitle1 pb-2">
            <v-row align="center" no-gutters>
              <v-col>{{ meal.recipe_name }}</v-col>
              <v-col v-if="meal.pinned" cols="auto">
                <v-icon small color="primary">{{ $globals.icons.pin }}</v-icon>
              </v-col>
            </v-row>
          </v-card-title>

          <!-- Date and Cook Time -->
          <v-card-subtitle class="pb-4">
            <div class="mb-2">
              <strong>{{ formatDate(meal.date) }}</strong>
            </div>
            <v-chip
              size="small"
              variant="outlined"
              class="mr-2"
            >
              <v-icon start small>{{ $globals.icons.clock }}</v-icon>
              {{ meal.cook_time }} min
            </v-chip>
            <v-chip
              size="small"
              variant="outlined"
            >
              <v-icon start small>{{ getDifficultyIcon(meal.difficulty) }}</v-icon>
              {{ meal.difficulty }}
            </v-chip>
          </v-card-subtitle>

          <!-- Description -->
          <v-card-text v-if="meal.description" class="text-caption pb-2 flex-grow-1">
            {{ truncate(meal.description, 80) }}
          </v-card-text>

          <!-- Dietary Tags -->
          <v-card-text v-if="meal.dietary_tags?.length" class="pb-2">
            <v-chip-group>
              <v-chip
                v-for="tag in meal.dietary_tags"
                :key="tag"
                size="x-small"
                variant="outlined"
              >
                {{ tag }}
              </v-chip>
            </v-chip-group>
          </v-card-text>

          <!-- Action Buttons -->
          <v-card-actions class="mt-auto">
            <v-spacer />
            <v-btn
              size="small"
              variant="text"
              @click="$emit('regenerate-day', idx)"
            >
              <v-icon start>{{ $globals.icons.refresh }}</v-icon>
              {{ $t('meal-randomizer.regenerate') }}
            </v-btn>
            <v-btn
              size="small"
              variant="text"
              :to="`/g/recipes/${meal.recipe_slug}`"
            >
              <v-icon start>{{ $globals.icons.eye }}</v-icon>
              {{ $t('common.view') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Save as Template -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card outlined>
          <v-card-title>{{ $t('meal-randomizer.save-as-template') }}</v-card-title>
          <v-card-text>
            <v-row align="center" gutter="2">
              <v-col>
                <v-text-field
                  v-model="templateName"
                  :label="$t('meal-randomizer.template-name')"
                  outlined
                  dense
                  placeholder="e.g., Summer Weeknights"
                />
              </v-col>
              <v-col cols="auto">
                <v-btn
                  color="primary"
                  @click="handleSaveTemplate"
                  :disabled="!templateName"
                >
                  {{ $t('common.save') }}
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import { defineNuxtComponent } from "#app";
import type { RandomizerResponse } from "~/lib/api/types/meal-randomizer";

export default defineNuxtComponent({
  emits: ["regenerate-day", "save-as-template"],
  props: {
    result: {
      type: Object as PropType<RandomizerResponse>,
      required: true,
    },
  },
  setup(props, { emit }) {
    const templateName = ref("");

    const formatDate = (dateStr: string) => {
      const date = new Date(dateStr);
      return new Intl.DateTimeFormat("en-US", {
        weekday: "long",
        month: "short",
        day: "numeric",
      }).format(date);
    };

    const truncate = (text: string, length: number) => {
      return text.length > length ? text.substring(0, length) + "..." : text;
    };

    const getDifficultyIcon = (difficulty: string) => {
      const iconMap: Record<string, string> = {
        easy: "mdiChefHat",
        medium: "mdiChefHat",
        complex: "mdiChefHat",
      };
      return iconMap[difficulty.toLowerCase()] || "mdiChefHat";
    };

    const handleSaveTemplate = () => {
      if (templateName.value.trim()) {
        emit("save-as-template", templateName.value);
        templateName.value = "";
      }
    };

    return {
      templateName,
      formatDate,
      truncate,
      getDifficultyIcon,
      handleSaveTemplate,
    };
  },
});
</script>

<style scoped>
</style>
