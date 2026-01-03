// src/core/sync/queue.ts
// SyncQueue - オフライン同期キュー管理
import { httpClient } from '@/core/http';
import { syncStorage } from './storage';
import type { SyncQueueItem, SyncResult, ConflictData } from './types';

const MAX_RETRIES = 3;

class SyncQueue {
  private static instance: SyncQueue;
  private isSyncing = false;
  private onConflictCallback: ((conflict: ConflictData) => void) | null = null;

  private constructor() {
    // オンライン復帰時に自動同期
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        this.sync();
      });
    }
  }

  static getInstance(): SyncQueue {
    if (!SyncQueue.instance) {
      SyncQueue.instance = new SyncQueue();
    }
    return SyncQueue.instance;
  }

  // 競合発生時のコールバックを設定
  onConflict(callback: (conflict: ConflictData) => void): void {
    this.onConflictCallback = callback;
  }

  // キューに追加
  async add(item: Omit<SyncQueueItem, 'id' | 'createdAt' | 'retryCount' | 'status'>): Promise<string> {
    const id = await syncStorage.addToQueue({
      ...item,
      status: 'pending',
    });

    // オンラインなら即座に同期開始
    if (navigator.onLine && !this.isSyncing) {
      this.sync();
    }

    return id;
  }

  // 同期を実行
  async sync(): Promise<SyncResult> {
    if (this.isSyncing || !navigator.onLine) {
      return {
        success: false,
        syncedCount: 0,
        conflictCount: 0,
        errorCount: 0,
        conflicts: [],
      };
    }

    this.isSyncing = true;
    const result: SyncResult = {
      success: true,
      syncedCount: 0,
      conflictCount: 0,
      errorCount: 0,
      conflicts: [],
    };

    try {
      const pendingItems = await syncStorage.getPendingItems();

      for (const item of pendingItems) {
        await this.processItem(item, result);
      }

      // 同期済みアイテムをクリア
      await syncStorage.clearSynced();

    } catch (error) {
      result.success = false;
      console.error('Sync failed:', error);
    } finally {
      this.isSyncing = false;
    }

    return result;
  }

  private async processItem(item: SyncQueueItem, result: SyncResult): Promise<void> {
    try {
      await syncStorage.updateStatus(item.id, 'syncing');

      const endpoint = this.getEndpoint(item);
      switch (item.operation) {
        case 'create':
          await httpClient.post(endpoint, item.payload);
          break;
        case 'update':
          await httpClient.put(
            `${endpoint}/${item.entityId}`,
            { ...item.payload, version: item.version }
          );
          break;
        case 'delete':
          await httpClient.delete(`${endpoint}/${item.entityId}`);
          break;
      }

      await syncStorage.updateStatus(item.id, 'synced');
      result.syncedCount++;

    } catch (error: unknown) {
      await this.handleError(item, error, result);
    }
  }

  private async handleError(
    item: SyncQueueItem,
    error: unknown,
    result: SyncResult
  ): Promise<void> {
    const appError = error as { code?: string; status?: number; details?: Record<string, unknown> };

    // バージョン競合
    if (appError.code === 'CONFLICT' || appError.status === 409) {
      await syncStorage.updateStatus(item.id, 'conflict');
      result.conflictCount++;

      const conflict: ConflictData = {
        queueItem: item,
        localData: item.payload,
        serverData: appError.details?.currentData as Record<string, unknown> || {},
        serverVersion: (appError.details?.currentVersion as number) || 0,
      };

      result.conflicts.push(conflict);
      this.onConflictCallback?.(conflict);
      return;
    }

    // リトライ可能なエラー
    if (item.retryCount < MAX_RETRIES) {
      await syncStorage.incrementRetry(item.id);
      await syncStorage.updateStatus(item.id, 'pending');
      return;
    }

    // 最大リトライ回数超過
    await syncStorage.updateStatus(
      item.id,
      'error',
      appError.code || 'Unknown error'
    );
    result.errorCount++;
  }

  private getEndpoint(item: SyncQueueItem): string {
    const endpoints: Record<string, string> = {
      match: '/matches',
      goal: '/goals',
      team: '/teams',
      player: '/players',
    };
    return endpoints[item.entityType] || `/${item.entityType}s`;
  }

  // 競合を解決（ローカルデータで上書き）
  async resolveConflictWithLocal(itemId: string): Promise<void> {
    const items = await syncStorage.getPendingItems();
    const item = items.find(i => i.id === itemId);

    if (item) {
      // 強制更新フラグを付けて再キュー
      await syncStorage.updateStatus(itemId, 'pending');
      item.payload = { ...item.payload, force: true };
    }
  }

  // 競合を解決（サーバーデータを採用）
  async resolveConflictWithServer(itemId: string): Promise<void> {
    await syncStorage.updateStatus(itemId, 'synced');
    await syncStorage.clearSynced();
  }
}

export const syncQueue = SyncQueue.getInstance();
