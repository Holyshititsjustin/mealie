import type { RequestResponse } from "~/lib/api/types/non-generated";
import { useRequests } from "~/composables/api/api-client";

export interface PantryItemOut {
  id: string;
  name: string;
  quantity: number;
  unit?: string | null;
  expiresAt: string;
  expiredAt?: string | null;
  depletedAt?: string | null;
  isArchived?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface PantryItemCreate {
  name: string;
  quantity: number;
  unit?: string | null;
  purchasedAt?: string | null;
  expiresAt: string;
}

export interface PantryItemUpdate extends Partial<PantryItemCreate> {}

const base = "/api/households/pantry";

export function usePantry() {
  const requests = useRequests();

  async function listItems(): Promise<RequestResponse<PantryItemOut[]>> {
    return await requests.get<PantryItemOut[]>(`${base}/items`);
  }

  async function getExpiring(): Promise<RequestResponse<PantryItemOut[]>> {
    return await requests.get<PantryItemOut[]>(`${base}/expiring`);
  }

  async function getExpired(): Promise<RequestResponse<PantryItemOut[]>> {
    return await requests.get<PantryItemOut[]>(`${base}/expired`);
  }

  async function createItem(payload: PantryItemCreate): Promise<RequestResponse<PantryItemOut>> {
    return await requests.post<PantryItemOut, PantryItemCreate>(`${base}/items`, payload);
  }

  async function updateItem(id: string, payload: PantryItemUpdate): Promise<RequestResponse<PantryItemOut>> {
    return await requests.put<PantryItemOut, PantryItemUpdate>(`${base}/items/${id}`, payload);
  }

  async function deleteItem(id: string): Promise<RequestResponse<{ success: boolean }>> {
    return await requests.delete<{ success: boolean }>(`${base}/items/${id}`);
  }

  async function decrement(id: string, amount = 1): Promise<RequestResponse<PantryItemOut>> {
    return await requests.post<PantryItemOut, {}>(`${base}/items/${id}/decrement`, {}, { params: { amount } });
  }

  async function consume(id: string): Promise<RequestResponse<PantryItemOut>> {
    return await requests.post<PantryItemOut, {}>(`${base}/items/${id}/consume`, {});
  }

  async function discard(id: string): Promise<RequestResponse<PantryItemOut>> {
    return await requests.post<PantryItemOut, {}>(`${base}/items/${id}/discard`, {});
  }

  return {
    listItems,
    getExpiring,
    getExpired,
    createItem,
    updateItem,
    deleteItem,
    decrement,
    consume,
    discard,
  };
}
