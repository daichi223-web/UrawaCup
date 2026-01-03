// src/core/http/utils.ts
// HTTPユーティリティ関数
import { AxiosRequestConfig } from 'axios';
import { httpClient } from './client';
import toast from 'react-hot-toast';

/**
 * APIエラーの型定義
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * API成功レスポンス
 */
export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
}

/**
 * APIエラーレスポンス
 */
export interface ApiErrorResponse {
  success: false;
  error: ApiError;
}

/**
 * API レスポンス型
 */
export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

/**
 * API レスポンスをラップするヘルパー
 */
export async function apiRequest<T>(
  request: Promise<{ data: T }>
): Promise<ApiResponse<T>> {
  try {
    const response = await request;
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : '不明なエラー';
    return {
      success: false,
      error: {
        code: 'UNKNOWN_ERROR',
        message,
      },
    };
  }
}

/**
 * ファイルアップロード用のリクエスト設定を生成
 */
export function createUploadConfig(
  onProgress?: (percent: number) => void
): AxiosRequestConfig {
  return {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  };
}

/**
 * ファイルダウンロード用のリクエスト
 */
export async function downloadFile(
  url: string,
  filename: string,
  options?: AxiosRequestConfig
): Promise<void> {
  try {
    const response = await httpClient.get(url, {
      ...options,
      responseType: 'blob',
    });

    // Blobからダウンロードリンクを作成
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'ダウンロードに失敗しました';
    toast.error(message);
    throw error;
  }
}

/**
 * リトライ付きリクエスト
 */
export async function retryRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error');

      // 認証エラー・権限エラーはリトライしない
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status && [401, 403, 404, 422].includes(status)) {
        throw error;
      }

      if (attempt < maxRetries) {
        console.log(`[API] リトライ ${attempt}/${maxRetries}...`);
        await new Promise((resolve) => setTimeout(resolve, delay * attempt));
      }
    }
  }

  throw lastError;
}
