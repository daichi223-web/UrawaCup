// src/core/errors/types.ts
// 統一エラー型定義

export type ErrorCode =
  | 'BAD_REQUEST'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'VERSION_CONFLICT'
  | 'LOCK_CONFLICT'
  | 'VALIDATION_ERROR'
  | 'OFFLINE'
  | 'SYNC_ERROR'
  | 'SERVER_ERROR'
  | 'UNKNOWN';

export interface AppError {
  code: ErrorCode;
  message: string;
  status: number;
  details?: Record<string, unknown>;
  retryable: boolean;
}

export function isAppError(error: unknown): error is AppError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error &&
    'status' in error &&
    'retryable' in error
  );
}
