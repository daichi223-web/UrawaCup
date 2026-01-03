import { create } from 'zustand'
import type {
  Match,
  MatchWithDetails,
  MatchScoreInput,
  GoalInput,
  MatchStatus,
  ApprovalStatus,
  MatchApprovalResponse,
  PendingMatchesResponse
} from '@shared/types'
import api from '@/core/http'
import toast from 'react-hot-toast'

/**
 * 試合管理状態
 */
interface MatchState {
  // 試合一覧
  matches: MatchWithDetails[]
  isLoading: boolean
  error: string | null

  // 承認待ち試合
  pendingApprovalMatches: MatchWithDetails[]
  pendingApprovalCount: number

  // 選択中の試合
  selectedMatch: MatchWithDetails | null
  isEditing: boolean

  // 得点入力中のデータ
  pendingGoals: GoalInput[]

  // アクション
  fetchMatches: (tournamentId: number, options?: { date?: string; venueId?: number; approvalStatus?: ApprovalStatus }) => Promise<void>
  selectMatch: (match: MatchWithDetails | null) => void
  updateMatchScore: (matchId: number, score: MatchScoreInput) => Promise<boolean>
  updateMatchStatus: (matchId: number, status: MatchStatus) => Promise<boolean>

  // 得点管理
  addPendingGoal: (goal: GoalInput) => void
  removePendingGoal: (index: number) => void
  updatePendingGoal: (index: number, goal: GoalInput) => void
  clearPendingGoals: () => void

  // ロック管理
  lockMatch: (matchId: number) => Promise<boolean>
  unlockMatch: (matchId: number) => Promise<boolean>

  // 承認フロー管理
  fetchPendingApprovalMatches: (tournamentId?: number, venueId?: number) => Promise<void>
  approveMatch: (matchId: number, userId: number) => Promise<boolean>
  rejectMatch: (matchId: number, userId: number, reason: string) => Promise<boolean>
  resubmitMatch: (matchId: number, userId: number) => Promise<boolean>

  // 編集モード
  setEditing: (isEditing: boolean) => void
  clearError: () => void
}

/**
 * 試合管理ストア
 * - 試合一覧の取得・更新
 * - スコア・得点の入力
 * - ロック機能
 */
export const useMatchStore = create<MatchState>((set, _get) => ({
  // 初期状態
  matches: [],
  isLoading: false,
  error: null,
  pendingApprovalMatches: [],
  pendingApprovalCount: 0,
  selectedMatch: null,
  isEditing: false,
  pendingGoals: [],

  /**
   * 試合一覧を取得
   */
  fetchMatches: async (tournamentId, options) => {
    set({ isLoading: true, error: null })
    try {
      const params = new URLSearchParams()
      if (options?.date) params.append('date', options.date)
      if (options?.venueId) params.append('venue_id', options.venueId.toString())
      if (options?.approvalStatus) params.append('approval_status', options.approvalStatus)

      const { data } = await api.get<MatchWithDetails[]>(
        `/tournaments/${tournamentId}/matches?${params}`
      )
      set({ matches: data, isLoading: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : '試合データの取得に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
    }
  },

  /**
   * 試合を選択
   */
  selectMatch: (match) => {
    set({ selectedMatch: match, pendingGoals: [] })
  },

  /**
   * 試合スコアを更新
   */
  updateMatchScore: async (matchId, score) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.put<Match>(`/matches/${matchId}/score`, score)

      // 一覧を更新
      set((state) => ({
        matches: state.matches.map((m) =>
          m.id === matchId ? { ...m, ...data } : m
        ),
        selectedMatch: state.selectedMatch?.id === matchId
          ? { ...state.selectedMatch, ...data }
          : state.selectedMatch,
        isLoading: false,
        pendingGoals: [],
        isEditing: false,
      }))

      toast.success('試合結果を保存しました')
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '試合結果の保存に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
      return false
    }
  },

  /**
   * 試合ステータスを更新
   */
  updateMatchStatus: async (matchId, status) => {
    try {
      await api.patch(`/matches/${matchId}/status`, { status })

      set((state) => ({
        matches: state.matches.map((m) =>
          m.id === matchId ? { ...m, status } : m
        ),
        selectedMatch: state.selectedMatch?.id === matchId
          ? { ...state.selectedMatch, status }
          : state.selectedMatch,
      }))

      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : 'ステータスの更新に失敗しました'
      toast.error(message)
      return false
    }
  },

  /**
   * 保留中の得点を追加
   */
  addPendingGoal: (goal) => {
    set((state) => ({
      pendingGoals: [...state.pendingGoals, goal].sort((a, b) => {
        // ハーフ → 時間でソート
        if (a.half !== b.half) return a.half - b.half
        return a.minute - b.minute
      }),
    }))
  },

  /**
   * 保留中の得点を削除
   */
  removePendingGoal: (index) => {
    set((state) => ({
      pendingGoals: state.pendingGoals.filter((_, i) => i !== index),
    }))
  },

  /**
   * 保留中の得点を更新
   */
  updatePendingGoal: (index, goal) => {
    set((state) => ({
      pendingGoals: state.pendingGoals.map((g, i) => (i === index ? goal : g)),
    }))
  },

  /**
   * 保留中の得点をクリア
   */
  clearPendingGoals: () => {
    set({ pendingGoals: [] })
  },

  /**
   * 試合をロック
   */
  lockMatch: async (matchId) => {
    try {
      await api.post(`/matches/${matchId}/lock`)

      set((state) => ({
        matches: state.matches.map((m) =>
          m.id === matchId ? { ...m, isLocked: true } : m
        ),
        selectedMatch: state.selectedMatch?.id === matchId
          ? { ...state.selectedMatch, isLocked: true }
          : state.selectedMatch,
      }))

      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : 'ロックに失敗しました'
      toast.error(message)
      return false
    }
  },

  /**
   * 試合のロックを解除
   */
  unlockMatch: async (matchId) => {
    try {
      await api.delete(`/matches/${matchId}/lock`)

      set((state) => ({
        matches: state.matches.map((m) =>
          m.id === matchId ? { ...m, isLocked: false } : m
        ),
        selectedMatch: state.selectedMatch?.id === matchId
          ? { ...state.selectedMatch, isLocked: false }
          : state.selectedMatch,
      }))

      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : 'ロック解除に失敗しました'
      toast.error(message)
      return false
    }
  },

  /**
   * 承認待ち試合一覧を取得
   */
  fetchPendingApprovalMatches: async (tournamentId, venueId) => {
    set({ isLoading: true, error: null })
    try {
      const params = new URLSearchParams()
      if (tournamentId) params.append('tournament_id', tournamentId.toString())
      if (venueId) params.append('venue_id', venueId.toString())

      const { data } = await api.get<PendingMatchesResponse>(
        `/matches/pending?${params}`
      )
      set({
        pendingApprovalMatches: data.matches,
        pendingApprovalCount: data.total,
        isLoading: false
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : '承認待ち試合の取得に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
    }
  },

  /**
   * 試合結果を承認
   */
  approveMatch: async (matchId, userId) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.post<MatchApprovalResponse>(
        `/matches/${matchId}/approve`,
        { user_id: userId }
      )

      // 承認待ち一覧から削除
      set((state) => ({
        pendingApprovalMatches: state.pendingApprovalMatches.filter(m => m.id !== matchId),
        pendingApprovalCount: state.pendingApprovalCount - 1,
        // メイン一覧も更新
        matches: state.matches.map(m =>
          m.id === matchId ? { ...m, approvalStatus: 'approved' as const } : m
        ),
        selectedMatch: state.selectedMatch?.id === matchId
          ? { ...state.selectedMatch, approvalStatus: 'approved' as const }
          : state.selectedMatch,
        isLoading: false,
      }))

      toast.success(data.message)
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '試合の承認に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
      return false
    }
  },

  /**
   * 試合結果を却下
   */
  rejectMatch: async (matchId, userId, reason) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.post<MatchApprovalResponse>(
        `/matches/${matchId}/reject`,
        { user_id: userId, reason }
      )

      // 承認待ち一覧から削除
      set((state) => ({
        pendingApprovalMatches: state.pendingApprovalMatches.filter(m => m.id !== matchId),
        pendingApprovalCount: state.pendingApprovalCount - 1,
        // メイン一覧も更新
        matches: state.matches.map(m =>
          m.id === matchId ? { ...m, approvalStatus: 'rejected' as const, rejectionReason: reason } : m
        ),
        selectedMatch: state.selectedMatch?.id === matchId
          ? { ...state.selectedMatch, approvalStatus: 'rejected' as const, rejectionReason: reason }
          : state.selectedMatch,
        isLoading: false,
      }))

      toast.success(data.message)
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '試合の却下に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
      return false
    }
  },

  /**
   * 却下された試合結果を再提出
   */
  resubmitMatch: async (matchId, userId) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.post<MatchApprovalResponse>(
        `/matches/${matchId}/resubmit?user_id=${userId}`
      )

      // 一覧を更新
      set((state) => ({
        matches: state.matches.map(m =>
          m.id === matchId ? { ...m, approvalStatus: 'pending' as const, rejectionReason: undefined } : m
        ),
        selectedMatch: state.selectedMatch?.id === matchId
          ? { ...state.selectedMatch, approvalStatus: 'pending' as const, rejectionReason: undefined }
          : state.selectedMatch,
        isLoading: false,
      }))

      toast.success(data.message)
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '試合の再提出に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
      return false
    }
  },

  /**
   * 編集モードの切り替え
   */
  setEditing: (isEditing) => {
    set({ isEditing })
  },

  /**
   * エラーのクリア
   */
  clearError: () => {
    set({ error: null })
  },
}))
