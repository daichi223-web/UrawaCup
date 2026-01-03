/**
 * 浦和カップ トーナメント管理システム - オフライン同期サービス
 *
 * オンライン復帰時にオフラインで行った操作をサーバーと同期
 * - Background Syncを活用
 * - 競合検出と解決
 * - リトライロジック
 */

import {
  db,
  type SyncQueueItem,
  getPendingSyncItems,
  updateSyncItemStatus,
  clearSyncedItems,
  addConflict,
  getPendingConflictsCount,
} from './db';
import { httpClient as apiClient } from '@/core/http';

// ============================================
// 同期サービスの設定
// ============================================

const SYNC_CONFIG = {
  /** 最大リトライ回数 */
  maxRetries: 5,
  /** リトライ間隔（ミリ秒、指数バックオフ） */
  retryDelayBase: 1000,
  /** 同期バッチサイズ */
  batchSize: 10,
};

// ============================================
// 同期ステータス管理
// ============================================

interface SyncState {
  isSyncing: boolean;
  lastSyncAt: Date | null;
  pendingCount: number;
  conflictCount: number;
  error: string | null;
}

let syncState: SyncState = {
  isSyncing: false,
  lastSyncAt: null,
  pendingCount: 0,
  conflictCount: 0,
  error: null,
};

type SyncListener = (state: SyncState) => void;
const listeners: Set<SyncListener> = new Set();

/**
 * 同期ステータスのリスナーを追加
 */
export function subscribeSyncState(listener: SyncListener): () => void {
  listeners.add(listener);
  // 現在のステートを即座に通知
  listener(syncState);
  return () => listeners.delete(listener);
}

/**
 * 同期ステータスを更新し、リスナーに通知
 */
function updateSyncState(updates: Partial<SyncState>) {
  syncState = { ...syncState, ...updates };
  listeners.forEach((listener) => listener(syncState));
}

/**
 * 現在の同期ステータスを取得
 */
export function getSyncState(): SyncState {
  return { ...syncState };
}

// ============================================
// 同期処理
// ============================================

/**
 * 同期キューの全アイテムを同期
 */
export async function syncAll(): Promise<void> {
  if (syncState.isSyncing) {
    console.log('[SyncService] 同期処理が既に実行中です');
    return;
  }

  if (!navigator.onLine) {
    console.log('[SyncService] オフラインのため同期をスキップ');
    return;
  }

  try {
    updateSyncState({ isSyncing: true, error: null });

    const pendingItems = await getPendingSyncItems();
    console.log(`[SyncService] ${pendingItems.length}件の同期待ちアイテム`);

    // バッチ処理
    for (let i = 0; i < pendingItems.length; i += SYNC_CONFIG.batchSize) {
      const batch = pendingItems.slice(i, i + SYNC_CONFIG.batchSize);
      await Promise.allSettled(batch.map(syncItem));
    }

    // 同期完了したアイテムを削除
    await clearSyncedItems();

    // 残りの保留アイテムと競合をカウント
    const pendingCount = await db.syncQueue
      .where('status')
      .anyOf(['pending', 'failed'])
      .count();
    const conflictCount = await getPendingConflictsCount();

    updateSyncState({
      isSyncing: false,
      lastSyncAt: new Date(),
      pendingCount,
      conflictCount,
    });

    console.log('[SyncService] 同期完了');
  } catch (error) {
    console.error('[SyncService] 同期エラー:', error);
    updateSyncState({
      isSyncing: false,
      error: error instanceof Error ? error.message : '同期中にエラーが発生しました',
    });
  }
}

/**
 * 単一アイテムの同期
 */
async function syncItem(item: SyncQueueItem): Promise<void> {
  if (!item.id) return;

  try {
    await updateSyncItemStatus(item.id, 'syncing');

    const response = await executeApiRequest(item);

    // 競合チェック（更新操作の場合）
    if (item.operation === 'update' && response.data) {
      const hasConflict = await checkForConflict(item, response.data);
      if (hasConflict) {
        // 競合を登録し、ステータスをpendingに戻す
        await updateSyncItemStatus(item.id, 'pending');
        return;
      }
    }

    await updateSyncItemStatus(item.id, 'synced');
    console.log(`[SyncService] アイテム ${item.id} 同期成功`);
  } catch (error) {
    console.error(`[SyncService] アイテム ${item.id} 同期失敗:`, error);
    const errorMessage = error instanceof Error ? error.message : '不明なエラー';
    await updateSyncItemStatus(item.id, 'failed', errorMessage);
  }
}

/**
 * APIリクエストを実行
 */
async function executeApiRequest(item: SyncQueueItem): Promise<{ data: unknown }> {
  const { endpoint, method, payload } = item;

  switch (method) {
    case 'POST':
      return await apiClient.post(endpoint, payload);
    case 'PUT':
      return await apiClient.put(endpoint, payload);
    case 'PATCH':
      return await apiClient.patch(endpoint, payload);
    case 'DELETE':
      return await apiClient.delete(endpoint);
    default:
      throw new Error(`サポートされていないHTTPメソッド: ${method}`);
  }
}

/**
 * 競合チェック
 */
async function checkForConflict(
  item: SyncQueueItem,
  serverData: unknown
): Promise<boolean> {
  // サーバーのデータとローカルのデータを比較
  const serverUpdatedAt = (serverData as { updated_at?: string })?.updated_at;
  const localUpdatedAt = (item.payload as { updatedAt?: string })?.updatedAt;

  if (!serverUpdatedAt || !localUpdatedAt) {
    return false;
  }

  const serverDate = new Date(serverUpdatedAt);
  const localDate = new Date(localUpdatedAt);

  // サーバーの方が新しい場合は競合
  if (serverDate > localDate) {
    await addConflict({
      entityType: item.entityType as 'match' | 'goal',
      entityId: item.entityId!,
      localData: item.payload,
      serverData,
      localUpdatedAt: localDate,
      serverUpdatedAt: serverDate,
    });
    return true;
  }

  return false;
}

// ============================================
// オンライン/オフラインイベント処理
// ============================================

/**
 * オンラインイベントハンドラ
 */
export function handleOnline(): void {
  console.log('[SyncService] オンラインになりました');
  // 少し待ってから同期開始（接続安定化のため）
  setTimeout(() => {
    syncAll();
  }, 1000);
}

/**
 * オフラインイベントハンドラ
 */
export function handleOffline(): void {
  console.log('[SyncService] オフラインになりました');
  updateSyncState({ error: null });
}

// ============================================
// 初期化
// ============================================

let isInitialized = false;

/**
 * 同期サービスを初期化
 */
export function initSyncService(): void {
  if (isInitialized) return;

  // オンライン/オフラインイベントリスナーを登録
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  // 初期ステートを設定
  updateSyncState({
    isSyncing: false,
    error: null,
  });

  // 初期化時にオンラインなら同期を試みる
  if (navigator.onLine) {
    syncAll();
  }

  isInitialized = true;
  console.log('[SyncService] 初期化完了');
}

/**
 * 同期サービスを破棄
 */
export function destroySyncService(): void {
  window.removeEventListener('online', handleOnline);
  window.removeEventListener('offline', handleOffline);
  listeners.clear();
  isInitialized = false;
}

// ============================================
// 試合データ専用の同期関数
// ============================================

/**
 * 試合結果をオフライン対応で保存
 */
export async function saveMatchResultOffline(
  matchId: number,
  data: unknown
): Promise<void> {
  // ローカルDBに保存
  await db.matches.update(matchId, {
    ...data as object,
    _localUpdatedAt: new Date(),
  });

  // 同期キューに追加
  await db.syncQueue.add({
    operation: 'update',
    entityType: 'match',
    entityId: matchId,
    payload: data,
    endpoint: `/api/v1/matches/${matchId}/score`,
    method: 'PUT',
    createdAt: new Date(),
    retryCount: 0,
    status: 'pending',
  });

  // 保留カウントを更新
  const pendingCount = await db.syncQueue
    .where('status')
    .anyOf(['pending', 'syncing'])
    .count();
  updateSyncState({ pendingCount });

  // オンラインなら即座に同期
  if (navigator.onLine) {
    syncAll();
  }
}

/**
 * 得点をオフライン対応で保存
 */
export async function saveGoalOffline(
  matchId: number,
  goalData: unknown
): Promise<number> {
  // ローカルDBに一時IDで保存
  const tempId = Date.now();
  await db.goals.add({
    id: tempId,
    matchId,
    ...goalData as object,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  } as Goal & { _localUpdatedAt?: Date });

  // 同期キューに追加
  await db.syncQueue.add({
    operation: 'create',
    entityType: 'goal',
    entityId: tempId,
    payload: { matchId, ...goalData as object },
    endpoint: `/api/v1/matches/${matchId}/goals`,
    method: 'POST',
    createdAt: new Date(),
    retryCount: 0,
    status: 'pending',
  });

  // 保留カウントを更新
  const pendingCount = await db.syncQueue
    .where('status')
    .anyOf(['pending', 'syncing'])
    .count();
  updateSyncState({ pendingCount });

  // オンラインなら即座に同期
  if (navigator.onLine) {
    syncAll();
  }

  return tempId;
}

// 型インポートのためのダミー
import type { Goal } from '@/types';
