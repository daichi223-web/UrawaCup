import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User, UserRole, LoginRequest, LoginResponse } from '@shared/types'
import api from '@/core/http'

/**
 * 認証状態の型定義
 */
interface AuthState {
  // 状態
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // アクション
  login: (credentials: LoginRequest) => Promise<boolean>
  logout: () => void
  checkAuth: () => Promise<void>
  clearError: () => void
  setUser: (user: User) => void

  // 権限チェック
  hasRole: (role: UserRole) => boolean
  canEditVenue: (venueId: number) => boolean
}

/**
 * 認証状態管理ストア
 * - ログイン/ログアウト
 * - 認証トークン管理
 * - 権限チェック
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初期状態
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      /**
       * ログイン処理
       */
      login: async (credentials: LoginRequest): Promise<boolean> => {
        set({ isLoading: true, error: null })
        try {
          const { data } = await api.post<LoginResponse>('/auth/login', credentials)

          set({
            user: data.user,
            accessToken: data.accessToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })

          // APIクライアントにトークンを設定
          api.defaults.headers.common['Authorization'] = `Bearer ${data.accessToken}`

          return true
        } catch (error) {
          const message = error instanceof Error ? error.message : 'ログインに失敗しました'
          set({
            user: null,
            accessToken: null,
            isAuthenticated: false,
            isLoading: false,
            error: message,
          })
          return false
        }
      },

      /**
       * ログアウト処理
       */
      logout: () => {
        // APIクライアントからトークンを削除
        delete api.defaults.headers.common['Authorization']

        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        })
      },

      /**
       * 認証状態の確認（トークン検証）
       * 開発モードではトークンがない場合に自動的に管理者としてログイン
       */
      checkAuth: async () => {
        const { accessToken, login } = get()

        // トークンがある場合は検証
        if (accessToken) {
          set({ isLoading: true })
          try {
            // トークンをヘッダーに設定
            api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`

            // ユーザー情報を取得して検証
            const { data } = await api.get<User>('/auth/me')
            set({
              user: data,
              isAuthenticated: true,
              isLoading: false,
            })
            return
          } catch {
            // トークンが無効な場合は続行（自動ログインを試みる）
          }
        }

        // 開発モード: 自動的に管理者としてログイン
        if (import.meta.env.DEV) {
          console.log('開発モード: 管理者として自動ログインを試行...')
          const success = await login({ username: 'admin', password: 'admin123' })
          if (success) {
            console.log('自動ログイン成功')
            return
          }
          console.log('自動ログイン失敗 - 手動でログインしてください')
        }

        set({ isAuthenticated: false, user: null, isLoading: false })
      },

      /**
       * エラーのクリア
       */
      clearError: () => {
        set({ error: null })
      },

      /**
       * ユーザー情報の更新
       */
      setUser: (user: User) => {
        set({ user })
      },

      /**
       * 権限チェック
       */
      hasRole: (role: UserRole): boolean => {
        const { user, isAuthenticated } = get()
        if (!isAuthenticated || !user) return false

        // 管理者は全権限を持つ
        if (user.role === 'admin') return true

        return user.role === role
      },

      /**
       * 特定会場の編集権限チェック
       */
      canEditVenue: (venueId: number): boolean => {
        const { user, isAuthenticated } = get()
        if (!isAuthenticated || !user) return false

        // 管理者は全会場を編集可能
        if (user.role === 'admin') return true

        // 会場担当者は担当会場のみ編集可能
        if (user.role === 'venue_staff' && user.venueId === venueId) return true

        return false
      },
    }),
    {
      name: 'urawa-cup-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
