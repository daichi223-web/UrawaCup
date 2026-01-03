/**
 * 浦和カップ トーナメント管理システム - アプリケーション状態管理
 *
 * Zustandを使用したグローバル状態管理
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { Tournament, AuthUser } from '@/types'

/**
 * アプリケーション状態の型定義
 */
interface AppState {
  // 認証状態
  user: AuthUser | null
  isAuthenticated: boolean
  accessToken: string | null

  // 現在の大会
  currentTournament: Tournament | null

  // UI状態
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'

  // オンライン状態
  isOnline: boolean
  isSyncing: boolean
  pendingOperationsCount: number
  lastSyncAt: string | null

  // アクション
  setUser: (user: AuthUser | null, token?: string | null) => void
  logout: () => void
  setCurrentTournament: (tournament: Tournament | null) => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  setOnlineStatus: (isOnline: boolean) => void
  setSyncStatus: (isSyncing: boolean) => void
  setPendingOperationsCount: (count: number) => void
  setLastSyncAt: (timestamp: string | null) => void
}

/**
 * アプリケーションストア
 */
export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // 初期状態
      user: null,
      isAuthenticated: false,
      accessToken: null,
      currentTournament: null,
      sidebarOpen: true,
      theme: 'system',
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
      isSyncing: false,
      pendingOperationsCount: 0,
      lastSyncAt: null,

      // 認証アクション
      setUser: (user, token = null) =>
        set({
          user,
          isAuthenticated: !!user,
          accessToken: token,
        }),

      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          accessToken: null,
        }),

      // 大会設定
      setCurrentTournament: (tournament) =>
        set({ currentTournament: tournament }),

      // UI操作
      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      setTheme: (theme) => set({ theme }),

      // オンライン状態
      setOnlineStatus: (isOnline) => set({ isOnline }),

      setSyncStatus: (isSyncing) => set({ isSyncing }),

      setPendingOperationsCount: (count) =>
        set({ pendingOperationsCount: count }),

      setLastSyncAt: (timestamp) => set({ lastSyncAt: timestamp }),
    }),
    {
      name: 'urawa-cup-app-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // 永続化する状態のみ選択
        user: state.user,
        accessToken: state.accessToken,
        currentTournament: state.currentTournament,
        sidebarOpen: state.sidebarOpen,
        theme: state.theme,
        lastSyncAt: state.lastSyncAt,
      }),
    }
  )
)

// オンラインステータスのリスナーを設定
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    useAppStore.getState().setOnlineStatus(true)
  })
  window.addEventListener('offline', () => {
    useAppStore.getState().setOnlineStatus(false)
  })
}

/**
 * 認証トークン取得用のヘルパー関数
 */
export const getAuthToken = (): string | null => {
  return useAppStore.getState().accessToken
}

/**
 * 現在の大会ID取得用のヘルパー関数
 */
export const getCurrentTournamentId = (): number | null => {
  return useAppStore.getState().currentTournament?.id ?? null
}
