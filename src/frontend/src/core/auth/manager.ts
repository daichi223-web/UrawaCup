// src/core/auth/manager.ts
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
