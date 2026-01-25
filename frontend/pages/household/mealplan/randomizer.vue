<template>
  <div class="pa-4">
    <h2 class="text-h5 mb-4">{{ $t('meal-randomizer.title') }}</h2>
    <!-- Mount the dialog component in open state to use as a full page -->
    <MealRandomizer v-model="open" />
  </div>
</template>

<script lang="ts" setup>
import MealRandomizer from "~/components/MealRandomizer/MealRandomizer.vue";
const open = ref(true);
</script>
