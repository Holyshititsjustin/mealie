<template>
  <div class="px-4 py-2">
    <h2 class="text-h5 mb-4">{{ $t('pantry.pantry') }}</h2>

    <v-tabs v-model="tab" class="mb-4">
      <v-tab value="items">{{ $t('pantry.items') }}</v-tab>
      <v-tab value="expiring">{{ $t('pantry.expiring') }}</v-tab>
      <v-tab value="history">{{ $t('pantry.history') }}</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="items">
        <v-alert type="info" variant="tonal" class="mb-3">
          Pantry UI scaffolded. API integration coming next.
        </v-alert>
        <v-card>
          <v-card-text>
            <div class="text-caption mb-2">Connected: {{ about?.version ? 'Yes' : 'Unknown' }}</div>
            <div class="d-flex align-center gap-2">
              <v-btn :to="'/shopping-lists'" color="primary" variant="elevated">
                {{ $t('shopping-list.shopping-lists') }}
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="expiring">
        <v-alert type="info" variant="tonal">Expiring items view will show soonest-expiring first.</v-alert>
      </v-window-item>

      <v-window-item value="history">
        <v-alert type="info" variant="tonal">History of pantry actions will appear here.</v-alert>
      </v-window-item>
    </v-window>
  </div>
</template>

<script lang="ts" setup>
const tab = ref<'items' | 'expiring' | 'history'>('items');

const about = ref<{ version?: string } | null>(null);
try {
  const { data } = await useFetch('/api/app/about');
  // @ts-expect-error runtime JSON
  about.value = data.value as any;
}
catch (e) {
  // ignore for scaffold
}
</script>
