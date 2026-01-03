// src/core/http/interceptors/error.ts
// エラー正規化インターセプター
import type { AxiosError } from 'axios';
import type { AppError, ErrorCode } from '@/core/errors';

function mapStatusToCode(status: number | undefined): ErrorCode {
  switch (status) {
    case 400: return 'BAD_REQUEST';
    case 401: return 'UNAUTHORIZED';
    case 403: return 'FORBIDDEN';
    case 404: return 'NOT_FOUND';
    case 409: return 'CONFLICT';
    case 422: return 'VALIDATION_ERROR';
    case 500:
    case 502:
    case 503: return 'SERVER_ERROR';
    default: return 'UNKNOWN';
  }
}

function extractMessage(error: AxiosError): string {
  const data = error.response?.data as Record<string, unknown> | undefined;

  // FastAPI形式対応: { detail: "..." } or { detail: [{ msg: "..." }] }
  if (data?.detail) {
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      return String(data.detail[0].msg);
    }
  }

  // 一般的な形式
  if (data?.message && typeof data.message === 'string') {
    return data.message;
  }
  if (data?.error && typeof data.error === 'object' && (data.error as Record<string, unknown>)?.message) {
    return String((data.error as Record<string, unknown>).message);
  }

  // デフォルトメッセージ
  return getDefaultMessage(error.response?.status);
}

function getDefaultMessage(status: number | undefined): string {
  switch (status) {
    case 400: return 'リクエストが不正です';
    case 401: return '認証が必要です';
    case 403: return 'アクセス権限がありません';
    case 404: return 'リソースが見つかりません';
    case 409: return '競合が発生しました';
    case 422: return '入力データが不正です';
    case 500: return 'サーバーエラーが発生しました';
    default: return 'エラーが発生しました';
  }
}

function isRetryable(status: number | undefined): boolean {
  return status === 500 || status === 502 || status === 503;
}

export function errorInterceptor(error: AxiosError): Promise<never> {
  // オフライン検出
  if (!navigator.onLine || error.code === 'ERR_NETWORK') {
    const offlineError: AppError = {
      code: 'OFFLINE',
      message: 'ネットワークに接続できません',
      status: 0,
      retryable: true,
    };
    return Promise.reject(offlineError);
  }

  const appError: AppError = {
    code: mapStatusToCode(error.response?.status),
    message: extractMessage(error),
    status: error.response?.status || 0,
    details: error.response?.data as Record<string, unknown> | undefined,
    retryable: isRetryable(error.response?.status),
  };

  return Promise.reject(appError);
}
