<template>
  <div class="px-4 py-2">
    <h2 class="text-h5 mb-4">{{ $t('pantry.pantry') }}</h2>

    <v-tabs v-model="tab" class="mb-4">
      <v-tab value="items">{{ $t('pantry.items') }}</v-tab>
      <v-tab value="expiring">{{ $t('pantry.expiring') }}</v-tab>
      <v-tab value="expired">{{ $t('pantry.expired') }}</v-tab>
      <v-tab value="history">{{ $t('pantry.history') }}</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="items">
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <span>{{ $t('pantry.items') }}</span>
            <div class="d-flex align-center gap-2">
              <v-btn color="primary" variant="elevated" @click="openCreateDialog">Add Item</v-btn>
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
                  <v-btn size="small" color="success" variant="tonal" @click="openConsumeDialog(item)">Consume</v-btn>
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
            <v-data-table :items="expiring" :headers="headers" item-key="id">
              <template #item.actions="{ item }">
                <div class="d-flex align-center gap-2">
                  <v-btn size="small" variant="tonal" @click="decrementItem(item, 1)">-1</v-btn>
                  <v-btn size="small" color="success" variant="tonal" @click="openConsumeDialog(item)">Consume</v-btn>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="expired">
        <v-card>
          <v-card-title>{{ $t('pantry.expired') }}</v-card-title>
          <v-card-text>
            <v-data-table :items="expired" :headers="headers" item-key="id">
              <template #item.actions="{ item }">
                <v-btn size="small" color="error" variant="tonal" @click="deleteItem(item.id)">Delete</v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="history">
        <v-alert type="info" variant="tonal">History of pantry actions will appear here.</v-alert>
      </v-window-item>
    </v-window>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="createDialogOpen" width="500">
      <v-card>
        <v-card-title>{{ editingItem ? 'Edit Item' : 'Add Pantry Item' }}</v-card-title>
        <v-card-text>
          <div class="d-flex flex-column gap-4 mt-4">
            <v-text-field v-model="form.name" label="Item Name" required />
            <v-row>
              <v-col>
                <v-text-field v-model.number="form.quantity" type="number" label="Quantity" required />
              </v-col>
              <v-col>
                <v-text-field v-model="form.unit" label="Unit (e.g., lbs, oz)" />
              </v-col>
            </v-row>
            <v-text-field v-model="form.expiresAt" type="date" label="Expires At" required />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="tonal" @click="createDialogOpen = false">Cancel</v-btn>
          <v-btn color="primary" variant="elevated" @click="saveItem">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Consume & Add to Shopping List Dialog -->
    <v-dialog v-model="consumeDialogOpen" width="500">
      <v-card>
        <v-card-title>Consume "{{ consumingItem?.name }}"</v-card-title>
        <v-card-text>
          <p class="mt-4">Add this item to your shopping list before marking as consumed?</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="tonal" @click="consumeDialogOpen = false">No</v-btn>
          <v-btn color="primary" variant="elevated" @click="consumeAndAddToList">Yes, Add to List</v-btn>
          <v-btn color="warning" variant="elevated" @click="consumeItem(consumingItem!)">Just Consume</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { usePantry, type PantryItemOut, type PantryItemCreate } from '~/composables/use-pantry';
import { useUserApi } from '~/composables/api';
import type { ShoppingListItemCreate } from '~/lib/api/types/household';
import { alert } from '~/composables/use-toast';

const tab = ref<'items' | 'expiring' | 'expired' | 'history'>('items');
const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Qty', key: 'quantity', align: 'end' },
  { title: 'Unit', key: 'unit' },
  { title: 'Expires', key: 'expiresAt' },
  { title: 'Actions', key: 'actions', sortable: false },
];

const items = ref<PantryItemOut[]>([]);
const expiring = ref<PantryItemOut[]>([]);
const expired = ref<PantryItemOut[]>([]);

const api = usePantry();
const userApi = useUserApi();

// Dialog state
const createDialogOpen = ref(false);
const consumeDialogOpen = ref(false);
const editingItem = ref<PantryItemOut | null>(null);
const consumingItem = ref<PantryItemOut | null>(null);
const form = ref<PantryItemCreate>({
  name: '',
  quantity: 1,
  unit: '',
  expiresAt: new Date().toISOString().split('T')[0],
});

async function refreshItems() {
  const { data } = await api.listItems();
  items.value = data ?? [];
}

async function refreshExpiring() {
  const { data } = await api.getExpiring();
  expiring.value = data ?? [];
}

async function refreshExpired() {
  const { data } = await api.getExpired();
  expired.value = data ?? [];
}

function resetForm() {
  editingItem.value = null;
  form.value = {
    name: '',
    quantity: 1,
    unit: '',
    expiresAt: new Date().toISOString().split('T')[0],
  };
}

function openCreateDialog() {
  resetForm();
  createDialogOpen.value = true;
}

async function saveItem() {
  try {
    if (editingItem.value) {
      await api.updateItem(editingItem.value.id, form.value);
      alert.success('Item updated');
    } else {
      await api.createItem(form.value);
      alert.success('Item created');
    }
    createDialogOpen.value = false;
    await Promise.all([refreshItems(), refreshExpiring(), refreshExpired()]);
  } catch (error) {
    alert.error('Failed to save item');
  }
}

async function decrementItem(item: PantryItemOut, amount: number) {
  const { data } = await api.decrement(item.id, amount);
  if (data) {
    await Promise.all([refreshItems(), refreshExpiring()]);
  }
}

function openConsumeDialog(item: PantryItemOut) {
  consumingItem.value = item;
  consumeDialogOpen.value = true;
}

async function consumeAndAddToList() {
  if (!consumingItem.value) return;
  try {
    // Get first shopping list (or create prompt to select one)
    const { data: lists } = await userApi.shopping.lists.getAll();
    if (!lists || lists.length === 0) {
      alert.error('No shopping lists found');
      return;
    }
    const listId = lists[0].id;
    
    // Add to shopping list
    const newItem: ShoppingListItemCreate = {
      title: consumingItem.value.name,
      quantity: consumingItem.value.quantity,
      unitId: undefined,
    };
    await userApi.shopping.items.create(listId, newItem);
    
    // Consume pantry item
    await api.consume(consumingItem.value.id);
    consumeDialogOpen.value = false;
    consumingItem.value = null;
    alert.success('Item added to shopping list and marked consumed');
    await Promise.all([refreshItems(), refreshExpiring(), refreshExpired()]);
  } catch (error) {
    alert.error('Failed to add to shopping list');
  }
}

async function consumeItem(item: PantryItemOut) {
  try {
    await api.consume(item.id);
    alert.success('Item marked consumed');
    await Promise.all([refreshItems(), refreshExpiring(), refreshExpired()]);
  } catch (error) {
    alert.error('Failed to consume item');
  }
}

async function discardItem(item: PantryItemOut) {
  try {
    await api.discard(item.id);
    alert.success('Item discarded');
    await Promise.all([refreshItems(), refreshExpiring(), refreshExpired()]);
  } catch (error) {
    alert.error('Failed to discard item');
  }
}

async function deleteItem(id: string) {
  try {
    await api.deleteItem(id);
    alert.success('Item deleted');
    await Promise.all([refreshItems(), refreshExpiring(), refreshExpired()]);
  } catch (error) {
    alert.error('Failed to delete item');
  }
}

onMounted(async () => {
  await Promise.all([refreshItems(), refreshExpiring(), refreshExpired()]);
});
</script>
