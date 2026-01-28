<template>
  <v-container fluid>
    <!-- Shopping List Summary -->
    <v-row class="mb-6">
      <v-col cols="12" md="6">
        <v-card outlined>
          <v-card-title>{{ $t('meal-randomizer.shopping-summary') }}</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item
                v-for="(count, category) in ingredientStats"
                :key="category"
              >
                <v-list-item-title>{{ category }}</v-list-item-title>
                <template #append>
                  <v-chip size="small" variant="outlined">{{ count }}</v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card outlined>
          <v-card-title>{{ $t('meal-randomizer.legend') }}</v-card-title>
          <v-card-text>
            <div class="mb-2">
              <v-icon size="small" color="primary">{{ $globals.icons.star }}</v-icon>
              <span class="ml-2">{{ $t('meal-randomizer.used-multiple-days') }}</span>
            </div>
            <div class="mb-2">
              <v-icon size="small" color="warning">{{ $globals.icons.alert }}</v-icon>
              <span class="ml-2">{{ $t('meal-randomizer.expiring-soon') }}</span>
            </div>
            <div>
              <v-icon size="small" color="success">{{ $globals.icons.check }}</v-icon>
              <span class="ml-2">{{ $t('meal-randomizer.substitution-available') }}</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Consolidated Shopping List -->
    <v-card outlined>
      <v-card-title>
        {{ $t('meal-randomizer.consolidated-ingredients') }}
      </v-card-title>
      <v-divider />

      <v-card-text class="pa-0">
        <v-table>
          <thead>
            <tr>
              <th>{{ $t('meal-randomizer.ingredient') }}</th>
              <th style="width: 100px">{{ $t('meal-randomizer.quantity') }}</th>
              <th>{{ $t('meal-randomizer.unit') }}</th>
              <th style="width: 120px">{{ $t('meal-randomizer.used-in') }}</th>
              <th v-if="hasExpiryData" style="width: 100px">{{ $t('meal-randomizer.expiry') }}</th>
              <th style="width: 100px">{{ $t('meal-randomizer.substitution') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in shoppingList" :key="idx">
              <td>
                <div class="d-flex align-center gap-2">
                  <v-icon
                    v-if="item.used_in_days?.length > 1"
                    size="small"
                    color="primary"
                  >
                    {{ $globals.icons.star }}
                  </v-icon>
                  <span>{{ item.name }}</span>
                </div>
              </td>
              <td>{{ formatQuantity(item.quantity) }}</td>
              <td>{{ item.unit || "as-is" }}</td>
              <td>
                <v-chip-group>
                  <v-chip
                    v-for="day in item.used_in_days"
                    :key="day"
                    size="x-small"
                    variant="outlined"
                  >
                    {{ abbreviateDay(day) }}
                  </v-chip>
                </v-chip-group>
              </td>
              <td v-if="hasExpiryData">
                <v-icon
                  v-if="isExpiring(item.expiry_date)"
                  size="small"
                  color="warning"
                >
                  {{ $globals.icons.alert }}
                </v-icon>
                <span v-else>-</span>
              </td>
              <td>
                <v-menu v-if="getSubstitution(item.name)">
                  <template #activator="{ props }">
                    <v-btn
                      size="x-small"
                      variant="outlined"
                      v-bind="props"
                    >
                      {{ $t('meal-randomizer.view') }}
                    </v-btn>
                  </template>
                  <v-card>
                    <v-card-text>
                      {{ getSubstitution(item.name)?.suggested_alternative }}
                    </v-card-text>
                  </v-card>
                </v-menu>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>

    <!-- Substitution Suggestions -->
    <v-row v-if="substitutions?.length" class="mt-6">
      <v-col cols="12">
        <v-card outlined>
          <v-card-title>
            <v-icon start>{{ $globals.icons.lightbulb }}</v-icon>
            {{ $t('meal-randomizer.substitution-suggestions') }}
          </v-card-title>
          <v-divider />

          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel
                v-for="(sub, idx) in substitutions"
                :key="idx"
              >
                <v-expansion-panel-title>
                  <v-icon start size="small" color="success">
                    {{ $globals.icons.check }}
                  </v-icon>
                  <strong class="ml-2">{{ sub.ingredient }}</strong>
                  <span class="text-caption ml-2">→ {{ sub.suggested_alternative }}</span>
                </v-expansion-panel-title>

                <v-expansion-panel-text>
                  <v-row class="pa-4" gutter="4">
                    <v-col cols="12" md="6">
                      <div>
                        <strong>{{ $t('meal-randomizer.reason') }}:</strong>
                        <p>{{ sub.reason }}</p>
                      </div>
                    </v-col>
                    <v-col cols="12" md="6">
                      <div>
                        <strong>{{ $t('meal-randomizer.estimated-savings') }}:</strong>
                        <p>{{ sub.estimated_savings }}</p>
                      </div>
                      <div>
                        <strong>{{ $t('meal-randomizer.nutritional-comparison') }}:</strong>
                        <p>{{ sub.nutritional_comparison }}</p>
                      </div>
                    </v-col>
                  </v-row>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Add to Shopping List Button -->
    <v-row class="mt-6">
      <v-col cols="12">
        <v-btn
          color="primary"
          block
          size="large"
          @click="addToShoppingList"
        >
          <v-icon start>{{ $globals.icons.plus }}</v-icon>
          {{ $t('meal-randomizer.add-to-shopping-list') }}
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import { defineNuxtComponent } from "#app";
import type { ConsolidatedIngredient, SubstitutionSuggestion } from "~/lib/api/types/meal-randomizer";
import { computed } from "vue";

export default defineNuxtComponent({
  props: {
    shoppingList: {
      type: Object as PropType<Record<string, ConsolidatedIngredient>>,
      required: true,
    },
    substitutions: {
      type: Array as PropType<SubstitutionSuggestion[]>,
      default: () => [],
    },
  },
  setup(props) {
    const toast = useToast();
    const { $axios } = useNuxtApp();
    const hasExpiryData = computed(() => {
      return Object.values(props.shoppingList).some((item) => item.expiry_date);
    });

    const ingredientStats = computed(() => {
      const stats: Record<string, number> = {};
      Object.values(props.shoppingList).forEach((item) => {
        const unitKey = item.unit || "as-is";
        stats[unitKey] = (stats[unitKey] || 0) + 1;
      });
      return stats;
    });

    const formatQuantity = (qty: number | string) => {
      if (typeof qty === "number") {
        return qty % 1 === 0 ? qty.toString() : qty.toFixed(2);
      }
      return qty;
    };

    const abbreviateDay = (dayName: string) => {
      return dayName.substring(0, 3).toUpperCase();
    };

    const isExpiring = (dateStr?: string) => {
      if (!dateStr) return false;
      const expiry = new Date(dateStr);
      const today = new Date();
      const daysUntilExpiry =
        (expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
      return daysUntilExpiry <= 3;
    };

    const getSubstitution = (ingredientName: string) => {
      return props.substitutions?.find(
        (sub) =>
          sub.ingredient.toLowerCase() === ingredientName.toLowerCase(),
      );
    };

    const addToShoppingList = async () => {
      if (!props.shoppingList || Object.keys(props.shoppingList).length === 0) {
        toast.error("No ingredients to add");
        return;
      }

      try {
        const items = Object.values(props.shoppingList).map((ingredient) => ({
          shopping_list_id: "", // Will use default list
          note: ingredient.name,
          quantity: ingredient.quantity,
          unit: ingredient.unit,
          is_checked: false,
        }));

        await $axios.post("/api/households/shopping/items/create-bulk", items);
        toast.success("Ingredients added to shopping list");
      } catch (error) {
        toast.error("Failed to add items to shopping list");
        console.error(error);
      }
    };

    return {
      hasExpiryData,
      ingredientStats,
      formatQuantity,
      abbreviateDay,
      isExpiring,
      getSubstitution,
      addToShoppingList,
    };
  },
});
</script>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}
</style>
