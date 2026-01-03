// src/core/http/interceptors/auth.ts
// 認証ヘッダー付与インターセプター
import type { InternalAxiosRequestConfig } from 'axios';
import { authManager } from '@/core/auth';

export function authInterceptor(
  config: InternalAxiosRequestConfig
): InternalAxiosRequestConfig {
  const token = authManager.getToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
}
