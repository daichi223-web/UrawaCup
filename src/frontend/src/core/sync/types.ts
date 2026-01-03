// src/core/sync/types.ts
// オフライン同期の型定義

export type SyncOperation = 'create' | 'update' | 'delete';
export type SyncStatus = 'pending' | 'syncing' | 'synced' | 'conflict' | 'error';

export interface SyncQueueItem {
  id: string;
  entityType: 'match' | 'goal' | 'team' | 'player';
  entityId: number | null;
  operation: SyncOperation;
  payload: Record<string, unknown>;
  version?: number;
  status: SyncStatus;
  errorMessage?: string;
  createdAt: Date;
  syncedAt?: Date;
  retryCount: number;
}

export interface ConflictData {
  queueItem: SyncQueueItem;
  localData: Record<string, unknown>;
  serverData: Record<string, unknown>;
  serverVersion: number;
}

export interface SyncResult {
  success: boolean;
  syncedCount: number;
  conflictCount: number;
  errorCount: number;
  conflicts: ConflictData[];
}
