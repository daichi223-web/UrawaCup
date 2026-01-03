"""
浦和カップ SDK生成エージェント - コード生成
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from string import Template

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    FRONTEND_SRC_PATH,
    TEMPLATE_DIR,
    OUTPUT_DIR,
    FEATURES,
    CORE_STRUCTURE,
    FEATURE_STRUCTURE,
)


class CodeGenerator:
    """コード生成クラス"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.frontend_src = FRONTEND_SRC_PATH
        self.template_dir = TEMPLATE_DIR

    def generate_core(self) -> List[str]:
        """コア基盤コードを生成"""
        generated_files = []

        # HTTPクライアント
        generated_files.extend(self._generate_http_client())

        # 認証管理
        generated_files.extend(self._generate_auth_manager())

        # エラー処理
        generated_files.extend(self._generate_error_types())

        # 設定
        generated_files.extend(self._generate_config())

        return generated_files

    def _generate_http_client(self) -> List[str]:
        """HTTPクライアントを生成"""
        files = []

        # client.ts
        client_code = '''// src/core/http/client.ts
// 唯一のHTTPクライアント - 全API呼び出しはこれを経由
import axios from 'axios';
import { authInterceptor } from './interceptors/auth';
import { errorInterceptor } from './interceptors/error';
import { transformInterceptor } from './interceptors/transform';

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// インターセプター登録（順序重要）
// 1. 認証ヘッダー付与
httpClient.interceptors.request.use(authInterceptor);

// 2. リクエスト: camelCase → snake_case
httpClient.interceptors.request.use(transformInterceptor.request);

// 3. レスポンス: snake_case → camelCase, エラー正規化
httpClient.interceptors.response.use(
  transformInterceptor.response,
  errorInterceptor
);

export { httpClient };
'''
        files.append(("core/http/client.ts", client_code))

        # interceptors/auth.ts
        auth_interceptor = '''// src/core/http/interceptors/auth.ts
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
'''
        files.append(("core/http/interceptors/auth.ts", auth_interceptor))

        # interceptors/transform.ts
        transform_interceptor = '''// src/core/http/interceptors/transform.ts
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
'''
        files.append(("core/http/interceptors/transform.ts", transform_interceptor))

        # interceptors/error.ts
        error_interceptor = '''// src/core/http/interceptors/error.ts
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
'''
        files.append(("core/http/interceptors/error.ts", error_interceptor))

        # index.ts
        http_index = '''// src/core/http/index.ts
export { httpClient } from './client';
export { authInterceptor } from './interceptors/auth';
export { errorInterceptor } from './interceptors/error';
export { transformInterceptor } from './interceptors/transform';
'''
        files.append(("core/http/index.ts", http_index))

        return files

    def _generate_auth_manager(self) -> List[str]:
        """認証管理コードを生成"""
        files = []

        # manager.ts
        manager_code = '''// src/core/auth/manager.ts
// 認証マネージャー（シングルトン）
const AUTH_STORAGE_KEY = 'urawa-cup-auth';

class AuthManager {
  private static instance: AuthManager;
  private accessToken: string | null = null;

  private constructor() {
    // localStorageから初期化
    this.loadFromStorage();
  }

  static getInstance(): AuthManager {
    if (!AuthManager.instance) {
      AuthManager.instance = new AuthManager();
    }
    return AuthManager.instance;
  }

  private loadFromStorage(): void {
    try {
      const authData = localStorage.getItem(AUTH_STORAGE_KEY);
      if (authData) {
        const parsed = JSON.parse(authData);
        if (parsed.state?.accessToken) {
          this.accessToken = parsed.state.accessToken;
        }
      }
    } catch {
      // パースエラーは無視
    }
  }

  setToken(token: string): void {
    this.accessToken = token;
    // Zustand storeと同期するため、storageも更新
    this.syncToStorage();
  }

  getToken(): string | null {
    // メモリにない場合はstorageから再読み込み
    if (!this.accessToken) {
      this.loadFromStorage();
    }
    return this.accessToken;
  }

  clearToken(): void {
    this.accessToken = null;
  }

  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  private syncToStorage(): void {
    // Zustand persist形式で保存
    const authData = {
      state: {
        accessToken: this.accessToken,
      },
      version: 0,
    };
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData));
  }
}

export const authManager = AuthManager.getInstance();
'''
        files.append(("core/auth/manager.ts", manager_code))

        # store.ts
        store_code = '''// src/core/auth/store.ts
// Zustand認証ストア
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authManager } from './manager';

interface User {
  id: number;
  username: string;
  displayName: string;
  role: 'admin' | 'venue_manager' | 'viewer';
  venueId?: number;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,

      login: (user, token) => {
        authManager.setToken(token);
        set({
          user,
          accessToken: token,
          isAuthenticated: true,
        });
      },

      logout: () => {
        authManager.clearToken();
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
        });
      },

      updateUser: (updates) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        }));
      },
    }),
    {
      name: 'urawa-cup-auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
'''
        files.append(("core/auth/store.ts", store_code))

        # index.ts
        auth_index = '''// src/core/auth/index.ts
export { authManager } from './manager';
export { useAuthStore } from './store';
'''
        files.append(("core/auth/index.ts", auth_index))

        return files

    def _generate_error_types(self) -> List[str]:
        """エラー型定義を生成"""
        files = []

        # types.ts
        types_code = '''// src/core/errors/types.ts
// 統一エラー型定義

export type ErrorCode =
  | 'BAD_REQUEST'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'VERSION_CONFLICT'
  | 'VALIDATION_ERROR'
  | 'OFFLINE'
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
'''
        files.append(("core/errors/types.ts", types_code))

        # handler.ts
        handler_code = '''// src/core/errors/handler.ts
// グローバルエラーハンドラ
import type { AppError, ErrorCode } from './types';
import { isAppError } from './types';

type ErrorCallback = (error: AppError) => void;

class ErrorHandler {
  private static instance: ErrorHandler;
  private callbacks: Map<ErrorCode | 'all', ErrorCallback[]> = new Map();

  private constructor() {}

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  // エラーハンドラを登録
  on(code: ErrorCode | 'all', callback: ErrorCallback): () => void {
    const callbacks = this.callbacks.get(code) || [];
    callbacks.push(callback);
    this.callbacks.set(code, callbacks);

    // クリーンアップ関数を返す
    return () => {
      const current = this.callbacks.get(code) || [];
      this.callbacks.set(
        code,
        current.filter((cb) => cb !== callback)
      );
    };
  }

  // エラーを処理
  handle(error: unknown): void {
    const appError = this.normalize(error);

    // 特定コードのハンドラを実行
    const codeCallbacks = this.callbacks.get(appError.code) || [];
    codeCallbacks.forEach((cb) => cb(appError));

    // 全体ハンドラを実行
    const allCallbacks = this.callbacks.get('all') || [];
    allCallbacks.forEach((cb) => cb(appError));
  }

  // エラーを正規化
  private normalize(error: unknown): AppError {
    if (isAppError(error)) {
      return error;
    }

    if (error instanceof Error) {
      return {
        code: 'UNKNOWN',
        message: error.message,
        status: 0,
        retryable: false,
      };
    }

    return {
      code: 'UNKNOWN',
      message: '予期しないエラーが発生しました',
      status: 0,
      retryable: false,
    };
  }
}

export const errorHandler = ErrorHandler.getInstance();
'''
        files.append(("core/errors/handler.ts", handler_code))

        # index.ts
        errors_index = '''// src/core/errors/index.ts
export type { AppError, ErrorCode } from './types';
export { isAppError } from './types';
export { errorHandler } from './handler';
'''
        files.append(("core/errors/index.ts", errors_index))

        return files

    def _generate_config(self) -> List[str]:
        """設定ファイルを生成"""
        files = []

        config_code = '''// src/core/config/index.ts
// 環境設定

export const config = {
  // API設定
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000,
  },

  // 大会固定情報
  tournament: {
    name: 'さいたま市招待高校サッカーフェスティバル浦和カップ',
    teamsCount: 24,
    groups: ['A', 'B', 'C', 'D'] as const,
    teamsPerGroup: 6,
    matchDuration: 50,
    halfDuration: 25,
    interval: 15,
    matchesPerDay: 6,
    days: 3,
  },

  // 会場担当校
  venueHosts: {
    A: '浦和南',
    B: '市立浦和',
    C: '浦和学院',
    D: '武南',
  } as const,

  // 順位決定ルール
  standingRules: [
    '勝点（勝利=3点、引分=1点、敗北=0点）',
    '得失点差',
    '総得点',
    '当該チーム間の対戦成績',
    '抽選',
  ],
} as const;

export type GroupName = (typeof config.tournament.groups)[number];
'''
        files.append(("core/config/index.ts", config_code))

        return files

    def generate_feature(self, feature_name: str) -> List[str]:
        """Featureモジュールを生成"""
        if feature_name not in FEATURES:
            raise ValueError(f"Unknown feature: {feature_name}")

        files = []
        pascal_name = "".join(word.capitalize() for word in feature_name.split("_"))
        singular_name = feature_name.rstrip("s")
        singular_pascal = "".join(word.capitalize() for word in singular_name.split("_"))

        # api.ts
        api_code = f'''// src/features/{feature_name}/api.ts
// {feature_name} API呼び出し
import {{ httpClient }} from '@/core/http';
import type {{ {singular_pascal}, Create{singular_pascal}Input, Update{singular_pascal}Input }} from './types';

export const {singular_name}Api = {{
  getAll: async () => {{
    const response = await httpClient.get<{singular_pascal}[]>('/{feature_name}');
    return response.data;
  }},

  getById: async (id: number) => {{
    const response = await httpClient.get<{singular_pascal}>(`/{feature_name}/${{id}}`);
    return response.data;
  }},

  create: async (data: Create{singular_pascal}Input) => {{
    const response = await httpClient.post<{singular_pascal}>('/{feature_name}', data);
    return response.data;
  }},

  update: async (id: number, data: Update{singular_pascal}Input) => {{
    const response = await httpClient.patch<{singular_pascal}>(`/{feature_name}/${{id}}`, data);
    return response.data;
  }},

  delete: async (id: number) => {{
    await httpClient.delete(`/{feature_name}/${{id}}`);
  }},
}};
'''
        files.append((f"features/{feature_name}/api.ts", api_code))

        # hooks.ts
        hooks_code = f'''// src/features/{feature_name}/hooks.ts
// {feature_name} React Query hooks
import {{ useQuery, useMutation, useQueryClient }} from '@tanstack/react-query';
import {{ {singular_name}Api }} from './api';
import type {{ Create{singular_pascal}Input, Update{singular_pascal}Input }} from './types';

const QUERY_KEY = ['{feature_name}'];

export function use{pascal_name}() {{
  return useQuery({{
    queryKey: QUERY_KEY,
    queryFn: () => {singular_name}Api.getAll(),
  }});
}}

export function use{singular_pascal}(id: number) {{
  return useQuery({{
    queryKey: [...QUERY_KEY, id],
    queryFn: () => {singular_name}Api.getById(id),
    enabled: id > 0,
  }});
}}

export function useCreate{singular_pascal}() {{
  const queryClient = useQueryClient();

  return useMutation({{
    mutationFn: (data: Create{singular_pascal}Input) => {singular_name}Api.create(data),
    onSuccess: () => {{
      queryClient.invalidateQueries({{ queryKey: QUERY_KEY }});
    }},
  }});
}}

export function useUpdate{singular_pascal}() {{
  const queryClient = useQueryClient();

  return useMutation({{
    mutationFn: ({{ id, data }}: {{ id: number; data: Update{singular_pascal}Input }}) =>
      {singular_name}Api.update(id, data),
    onSuccess: () => {{
      queryClient.invalidateQueries({{ queryKey: QUERY_KEY }});
    }},
  }});
}}

export function useDelete{singular_pascal}() {{
  const queryClient = useQueryClient();

  return useMutation({{
    mutationFn: (id: number) => {singular_name}Api.delete(id),
    onSuccess: () => {{
      queryClient.invalidateQueries({{ queryKey: QUERY_KEY }});
    }},
  }});
}}
'''
        files.append((f"features/{feature_name}/hooks.ts", hooks_code))

        # types.ts
        types_code = f'''// src/features/{feature_name}/types.ts
// {feature_name} 型定義

export interface {singular_pascal} {{
  id: number;
  // TODO: Add specific fields based on database structure
  createdAt: string;
  updatedAt: string;
}}

export interface Create{singular_pascal}Input {{
  // TODO: Add create input fields
}}

export interface Update{singular_pascal}Input {{
  // TODO: Add update input fields
}}
'''
        files.append((f"features/{feature_name}/types.ts", types_code))

        # index.ts
        index_code = f'''// src/features/{feature_name}/index.ts
export {{ {singular_name}Api }} from './api';
export {{
  use{pascal_name},
  use{singular_pascal},
  useCreate{singular_pascal},
  useUpdate{singular_pascal},
  useDelete{singular_pascal},
}} from './hooks';
export type {{ {singular_pascal}, Create{singular_pascal}Input, Update{singular_pascal}Input }} from './types';
'''
        files.append((f"features/{feature_name}/index.ts", index_code))

        return files

    def write_files(self, files: List[tuple], base_path: Optional[Path] = None) -> List[str]:
        """ファイルを出力"""
        base = base_path or self.output_dir
        written = []

        for rel_path, content in files:
            full_path = base / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            written.append(str(full_path))
            print(f"Generated: {rel_path}")

        return written


if __name__ == "__main__":
    generator = CodeGenerator()

    print("=== Core生成 ===")
    core_files = generator.generate_core()
    for path, _ in core_files:
        print(f"  {path}")

    print("\n=== Feature生成（teams）===")
    feature_files = generator.generate_feature("teams")
    for path, _ in feature_files:
        print(f"  {path}")
