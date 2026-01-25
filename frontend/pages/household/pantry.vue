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
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <span>{{ $t('pantry.items') }}</span>
            <div class="d-flex align-center gap-2">
              <v-btn color="primary" variant="elevated" @click="refreshItems">Refresh</v-btn>
              <v-btn :to="'/shopping-lists'" color="secondary" variant="tonal">
                {{ $t('shopping-list.shopping-lists') }}
              </v-btn>
            </div>
          </v-card-title>
          <v-card-text>
            <v-data-table :items="items" :headers="headers" item-key="id">
              <template #item.actions="{ item }">
                <div class="d-flex align-center gap-2">
                  <v-btn size="small" variant="tonal" @click="decrementItem(item, 1)">-1</v-btn>
                  <v-btn size="small" color="success" variant="tonal" @click="consumeItem(item)">Consume</v-btn>
                  <v-btn size="small" color="error" variant="tonal" @click="discardItem(item)">Discard</v-btn>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="expiring">
        <v-card>
          <v-card-title>{{ $t('pantry.expiring') }}</v-card-title>
          <v-card-text>
            <v-data-table :items="expiring" :headers="headers" item-key="id" />
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="history">
        <v-alert type="info" variant="tonal">History of pantry actions will appear here.</v-alert>
      </v-window-item>
    </v-window>
  </div>
</template>

<script lang="ts" setup>
import { usePantry, type PantryItemOut } from '~/composables/use-pantry';

const tab = ref<'items' | 'expiring' | 'history'>('items');
const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Qty', key: 'quantity', align: 'end' },
  { title: 'Unit', key: 'unit' },
  { title: 'Expires', key: 'expiresAt' },
  { title: 'Actions', key: 'actions', sortable: false },
];

const items = ref<PantryItemOut[]>([]);
const expiring = ref<PantryItemOut[]>([]);

const api = usePantry();

async function refreshItems() {
  const { data } = await api.listItems();
  items.value = data ?? [];
}

async function refreshExpiring() {
  const { data } = await api.getExpiring();
  expiring.value = data ?? [];
}

async function decrementItem(item: PantryItemOut, amount: number) {
  const { data } = await api.decrement(item.id, amount);
  if (data) {
    await refreshItems();
    await refreshExpiring();
  }
}

async function consumeItem(item: PantryItemOut) {
  const { data } = await api.consume(item.id);
  if (data) {
    await refreshItems();
    await refreshExpiring();
  }
}

async function discardItem(item: PantryItemOut) {
  const { data } = await api.discard(item.id);
  if (data) {
    await refreshItems();
    await refreshExpiring();
  }
}

onMounted(async () => {
  await Promise.all([refreshItems(), refreshExpiring()]);
});
</script>
