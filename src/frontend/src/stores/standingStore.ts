import { create } from 'zustand'
import type { GroupStanding, Standing, StandingWithTeam } from '@shared/types'
import api from '@/core/http'
import toast from 'react-hot-toast'

/**
 * 順位表管理状態
 */
interface StandingState {
  // グループ別順位表
  groupStandings: GroupStanding[]
  isLoading: boolean
  error: string | null

  // アクション
  fetchStandings: (tournamentId: number) => Promise<void>
  fetchGroupStanding: (tournamentId: number, groupId: string) => Promise<void>
  recalculateStandings: (tournamentId: number) => Promise<boolean>

  // ユーティリティ
  getGroupStanding: (groupId: string) => GroupStanding | undefined
  getGroupRank: (groupId: string, rank: number) => StandingWithTeam | undefined
  clearError: () => void
}

/**
 * 順位表管理ストア
 * - 全グループ順位表の取得
 * - リアルタイム更新
 * - 順位計算
 */
export const useStandingStore = create<StandingState>((set, get) => ({
  // 初期状態
  groupStandings: [],
  isLoading: false,
  error: null,

  /**
   * 全グループの順位表を取得
   */
  fetchStandings: async (tournamentId) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.get<GroupStanding[]>(
        `/tournaments/${tournamentId}/standings`
      )
      set({ groupStandings: data, isLoading: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : '順位表の取得に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
    }
  },

  /**
   * 特定グループの順位表を取得
   */
  fetchGroupStanding: async (tournamentId, groupId) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.get<GroupStanding>(
        `/tournaments/${tournamentId}/standings/${groupId}`
      )

      set((state) => ({
        groupStandings: state.groupStandings.map((gs) =>
          gs.group.id === groupId ? data : gs
        ),
        isLoading: false,
      }))
    } catch (error) {
      const message = error instanceof Error ? error.message : '順位表の取得に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
    }
  },

  /**
   * 順位を再計算
   */
  recalculateStandings: async (tournamentId) => {
    set({ isLoading: true })
    try {
      await api.post(`/tournaments/${tournamentId}/standings/recalculate`)

      // 再計算後に最新データを取得
      await get().fetchStandings(tournamentId)

      toast.success('順位表を再計算しました')
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '順位表の再計算に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
      return false
    }
  },

  /**
   * グループ別順位表を取得
   */
  getGroupStanding: (groupId) => {
    return get().groupStandings.find((gs) => gs.group.id === groupId)
  },

  /**
   * グループ内の特定順位のチームを取得
   */
  getGroupRank: (groupId, rank) => {
    const groupStanding = get().getGroupStanding(groupId)
    return groupStanding?.standings.find((s) => s.rank === rank)
  },

  /**
   * エラーのクリア
   */
  clearError: () => {
    set({ error: null })
  },
}))

/**
 * WebSocket経由で順位表が更新された時のハンドラ
 */
export function handleStandingUpdate(groupId: string, standings: Standing[]) {
  useStandingStore.setState((state) => ({
    groupStandings: state.groupStandings.map((gs) =>
      gs.group.id === groupId
        ? { ...gs, standings: standings as StandingWithTeam[] }
        : gs
    ),
  }))
}
