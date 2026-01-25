<template>
  <v-container fluid>
    <v-row gutter="4">
      <v-col v-if="templates?.length === 0" cols="12">
        <v-alert
          type="info"
          :icon="$globals.icons.information"
        >
          {{ $t('meal-randomizer.no-templates') }}
        </v-alert>
      </v-col>

      <v-col
        v-for="template in templates"
        :key="template.id"
        cols="12"
        sm="6"
        lg="4"
      >
        <v-card outlined class="h-100 d-flex flex-column">
          <v-card-title>{{ template.template_name }}</v-card-title>

          <v-card-subtitle>
            {{ $t('meal-randomizer.saved') }}:
            {{ formatDate(template.created_at) }}
          </v-card-subtitle>

          <v-card-text class="flex-grow-1">
            <v-list v-if="template.recipe_names?.length" density="compact">
              <v-list-item
                v-for="(recipe, idx) in template.recipe_names.slice(0, 5)"
                :key="idx"
                density="compact"
              >
                <template #prepend>
                  <v-icon size="small">{{ $globals.icons.check }}</v-icon>
                </template>
                <v-list-item-title class="text-caption">
                  {{ recipe }}
                </v-list-item-title>
              </v-list-item>
            </v-list>

            <v-list v-else density="compact">
              <v-list-item density="compact">
                <v-list-item-title class="text-caption text-disabled">
                  {{ $t('meal-randomizer.no-recipes') }}
                </v-list-item-title>
              </v-list-item>
            </v-list>

            <v-divider v-if="template.recipe_names?.length > 5" class="my-2" />

            <p v-if="(template.recipe_names?.length || 0) > 5" class="text-caption text-disabled">
              {{ $t('meal-randomizer.and-more', { count: template.recipe_names.length - 5 }) }}
            </p>
          </v-card-text>

          <v-card-actions>
            <v-spacer />
            <v-btn
              size="small"
              variant="outlined"
              color="primary"
              @click="$emit('load-template', template.id)"
            >
              <v-icon start>{{ $globals.icons.download }}</v-icon>
              {{ $t('meal-randomizer.load') }}
            </v-btn>
            <v-btn
              size="small"
              variant="text"
              color="error"
              @click="deleteTemplate(template.id)"
            >
              <v-icon>{{ $globals.icons.delete }}</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Delete Confirmation Dialog -->
    <v-dialog
      v-model="deleteConfirm.open"
      max-width="400"
    >
      <v-card>
        <v-card-title>{{ $t('meal-randomizer.delete-template') }}</v-card-title>
        <v-card-text>
          {{ $t('meal-randomizer.delete-template-confirm') }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="deleteConfirm.open = false"
          >
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn
            color="error"
            @click="confirmDelete"
          >
            {{ $t('common.delete') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang="ts">
import { defineNuxtComponent } from "#app";

export default defineNuxtComponent({
  emits: ["load-template"],
  props: {
    templates: {
      type: Array as PropType<any[]>,
      default: () => [],
    },
  },
  setup(props, { emit }) {
    const { $axios } = useNuxtApp();

    const deleteConfirm = reactive({
      open: false,
      templateId: null as string | null,
    });

    const formatDate = (dateStr: string) => {
      const date = new Date(dateStr);
      return new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      }).format(date);
    };

    const deleteTemplate = (templateId: string) => {
      deleteConfirm.templateId = templateId;
      deleteConfirm.open = true;
    };

    const confirmDelete = async () => {
      if (!deleteConfirm.templateId) return;

      try {
        await $axios.delete(
          `/api/v1/households/meals/randomizer/templates/${deleteConfirm.templateId}`,
        );
        deleteConfirm.open = false;
        // Emit event to parent to refresh templates list
        emit("load-template", "refresh");
      } catch (error) {
        console.error("Error deleting template:", error);
        // TODO: Show error toast
      }
    };

    return {
      deleteConfirm,
      formatDate,
      deleteTemplate,
      confirmDelete,
    };
  },
});
</script>

<style scoped>
</style>
