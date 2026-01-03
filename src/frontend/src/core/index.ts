// src/core/index.ts
// コアモジュール統一エクスポート

// HTTP クライアント
export { httpClient } from './http';

// 認証
export { authManager, useAuthStore } from './auth';

// エラー
export { errorHandler, isAppError } from './errors';
export type { AppError, ErrorCode } from './errors';

// 同期
export { syncQueue, syncStorage } from './sync';
export type { SyncQueueItem, SyncResult, ConflictData } from './sync';

// 設定
export { config } from './config';
export type { GroupName } from './config';
