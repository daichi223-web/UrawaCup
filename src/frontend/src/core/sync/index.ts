// src/core/sync/index.ts
export { syncQueue } from './queue';
export { syncStorage, syncDb } from './storage';
export { tryAutoMerge, formatConflictForDisplay, mergeWithSelections } from './conflict';
export type {
  SyncQueueItem,
  SyncOperation,
  SyncStatus,
  SyncResult,
  ConflictData,
} from './types';
export type { ConflictResolution, MergeResult } from './conflict';
