// src/core/sync/storage.ts
// IndexedDB操作
import Dexie, { Table } from 'dexie';
import type { SyncQueueItem, SyncStatus } from './types';

// Dexie拡張クラス
class SyncDatabase extends Dexie {
  syncQueue!: Table<SyncQueueItem>;
  matchCache!: Table<{ id: number; data: Record<string, unknown>; updatedAt: Date }>;
  standingCache!: Table<{ id: string; data: Record<string, unknown>; updatedAt: Date }>;

  constructor() {
    super('UrawaCupSync');

    this.version(1).stores({
      syncQueue: 'id, entityType, entityId, status, createdAt',
      matchCache: 'id, updatedAt',
      standingCache: 'id, updatedAt',
    });
  }
}

export const syncDb = new SyncDatabase();

export const syncStorage = {
  // キューアイテムを追加
  async addToQueue(item: Omit<SyncQueueItem, 'id' | 'createdAt' | 'retryCount'>): Promise<string> {
    const id = `${item.entityType}-${item.entityId || 'new'}-${Date.now()}`;
    await syncDb.syncQueue.add({
      ...item,
      id,
      createdAt: new Date(),
      retryCount: 0,
    });
    return id;
  },

  // ペンディングアイテムを取得
  async getPendingItems(): Promise<SyncQueueItem[]> {
    return syncDb.syncQueue
      .where('status')
      .equals('pending')
      .toArray();
  },

  // ステータスを更新
  async updateStatus(id: string, status: SyncStatus, errorMessage?: string): Promise<void> {
    await syncDb.syncQueue.update(id, {
      status,
      errorMessage,
      syncedAt: status === 'synced' ? new Date() : undefined,
    });
  },

  // リトライカウントを増加
  async incrementRetry(id: string): Promise<void> {
    const item = await syncDb.syncQueue.get(id);
    if (item) {
      await syncDb.syncQueue.update(id, {
        retryCount: item.retryCount + 1,
      });
    }
  },

  // 同期済みアイテムを削除
  async clearSynced(): Promise<void> {
    await syncDb.syncQueue
      .where('status')
      .equals('synced')
      .delete();
  },

  // キャッシュに保存
  async cacheMatch(id: number, data: Record<string, unknown>): Promise<void> {
    await syncDb.matchCache.put({
      id,
      data,
      updatedAt: new Date(),
    });
  },

  // キャッシュから取得
  async getMatchFromCache(id: number): Promise<Record<string, unknown> | null> {
    const cached = await syncDb.matchCache.get(id);
    return cached?.data || null;
  },

  // 全データをクリア
  async clearAll(): Promise<void> {
    await syncDb.syncQueue.clear();
    await syncDb.matchCache.clear();
    await syncDb.standingCache.clear();
  },
};
