// src/core/http/interceptors/transform.ts
// 命名規則自動変換インターセプター
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';

// snake_case → camelCase
function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

// camelCase → snake_case
function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

// オブジェクトのキーを変換
function transformKeys(
  obj: unknown,
  transformer: (key: string) => string
): unknown {
  if (Array.isArray(obj)) {
    return obj.map(item => transformKeys(item, transformer));
  }

  // Blob, File, ArrayBuffer, FormData などのバイナリデータはそのまま返す
  if (
    obj instanceof Blob ||
    obj instanceof File ||
    obj instanceof ArrayBuffer ||
    obj instanceof FormData
  ) {
    return obj;
  }

  if (obj !== null && typeof obj === 'object' && !(obj instanceof Date)) {
    return Object.keys(obj).reduce((acc, key) => {
      const newKey = transformer(key);
      acc[newKey] = transformKeys((obj as Record<string, unknown>)[key], transformer);
      return acc;
    }, {} as Record<string, unknown>);
  }

  return obj;
}

export const transformInterceptor = {
  request: (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    // リクエストデータ: camelCase → snake_case
    if (config.data) {
      config.data = transformKeys(config.data, camelToSnake);
    }
    if (config.params) {
      config.params = transformKeys(config.params, camelToSnake);
    }
    return config;
  },

  response: (response: AxiosResponse): AxiosResponse => {
    // レスポンスデータ: snake_case → camelCase
    if (response.data) {
      response.data = transformKeys(response.data, snakeToCamel);
    }
    return response;
  },
};
