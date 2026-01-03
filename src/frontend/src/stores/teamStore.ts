import { create } from 'zustand'
import type { Team, TeamWithDetails, TeamCreate, TeamUpdate, Player, PlayerCreate } from '@shared/types'
import api from '@/core/http'
import toast from 'react-hot-toast'

/**
 * チーム管理状態
 */
interface TeamState {
  // チーム一覧
  teams: Team[]
  isLoading: boolean
  error: string | null

  // 選択中のチーム（詳細表示・編集用）
  selectedTeam: TeamWithDetails | null

  // アクション
  fetchTeams: (tournamentId: number) => Promise<void>
  fetchTeamDetail: (teamId: number) => Promise<void>
  createTeam: (team: TeamCreate) => Promise<boolean>
  updateTeam: (teamId: number, team: TeamUpdate) => Promise<boolean>
  deleteTeam: (teamId: number) => Promise<boolean>
  selectTeam: (team: TeamWithDetails | null) => void

  // 選手管理
  addPlayer: (teamId: number, player: PlayerCreate) => Promise<boolean>
  updatePlayer: (playerId: number, player: Partial<Player>) => Promise<boolean>
  deletePlayer: (playerId: number) => Promise<boolean>
  importPlayers: (teamId: number, file: File) => Promise<boolean>

  // ユーティリティ
  getTeamsByGroup: (groupId: string) => Team[]
  clearError: () => void
}

/**
 * チーム管理ストア
 * - チームのCRUD
 * - 選手管理
 * - グループ別フィルタリング
 */
export const useTeamStore = create<TeamState>((set, get) => ({
  // 初期状態
  teams: [],
  isLoading: false,
  error: null,
  selectedTeam: null,

  /**
   * チーム一覧を取得
   */
  fetchTeams: async (tournamentId) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.get<{ teams: Team[]; total: number }>(`/teams/?tournament_id=${tournamentId}`)
      set({ teams: data.teams, isLoading: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'チームデータの取得に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
    }
  },

  /**
   * チーム詳細を取得
   */
  fetchTeamDetail: async (teamId) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.get<TeamWithDetails>(`/teams/${teamId}`)
      set({ selectedTeam: data, isLoading: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'チーム詳細の取得に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
    }
  },

  /**
   * チームを作成
   */
  createTeam: async (team) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.post<Team>('/teams', team)
      set((state) => ({
        teams: [...state.teams, data],
        isLoading: false,
      }))
      toast.success('チームを作成しました')
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : 'チームの作成に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
      return false
    }
  },

  /**
   * チームを更新
   */
  updateTeam: async (teamId, team) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.patch<Team>(`/teams/${teamId}`, team)
      set((state) => ({
        teams: state.teams.map((t) => (t.id === teamId ? data : t)),
        selectedTeam: state.selectedTeam?.id === teamId
          ? { ...state.selectedTeam, ...data }
          : state.selectedTeam,
        isLoading: false,
      }))
      toast.success('チーム情報を更新しました')
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : 'チームの更新に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
      return false
    }
  },

  /**
   * チームを削除
   */
  deleteTeam: async (teamId) => {
    set({ isLoading: true, error: null })
    try {
      await api.delete(`/teams/${teamId}`)
      set((state) => ({
        teams: state.teams.filter((t) => t.id !== teamId),
        selectedTeam: state.selectedTeam?.id === teamId ? null : state.selectedTeam,
        isLoading: false,
      }))
      toast.success('チームを削除しました')
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : 'チームの削除に失敗しました'
      set({ error: message, isLoading: false })
      toast.error(message)
      return false
    }
  },

  /**
   * チームを選択
   */
  selectTeam: (team) => {
    set({ selectedTeam: team })
  },

  /**
   * 選手を追加
   */
  addPlayer: async (teamId, player) => {
    try {
      const { data } = await api.post<Player>(`/teams/${teamId}/players`, player)

      set((state) => ({
        selectedTeam: state.selectedTeam?.id === teamId
          ? {
              ...state.selectedTeam,
              players: [...state.selectedTeam.players, data],
            }
          : state.selectedTeam,
      }))

      toast.success('選手を追加しました')
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '選手の追加に失敗しました'
      toast.error(message)
      return false
    }
  },

  /**
   * 選手を更新
   */
  updatePlayer: async (playerId, player) => {
    try {
      const { data } = await api.patch<Player>(`/players/${playerId}`, player)

      set((state) => ({
        selectedTeam: state.selectedTeam
          ? {
              ...state.selectedTeam,
              players: state.selectedTeam.players.map((p) =>
                p.id === playerId ? data : p
              ),
            }
          : null,
      }))

      toast.success('選手情報を更新しました')
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '選手の更新に失敗しました'
      toast.error(message)
      return false
    }
  },

  /**
   * 選手を削除
   */
  deletePlayer: async (playerId) => {
    try {
      await api.delete(`/players/${playerId}`)

      set((state) => ({
        selectedTeam: state.selectedTeam
          ? {
              ...state.selectedTeam,
              players: state.selectedTeam.players.filter((p) => p.id !== playerId),
            }
          : null,
      }))

      toast.success('選手を削除しました')
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '選手の削除に失敗しました'
      toast.error(message)
      return false
    }
  },

  /**
   * 選手をCSVからインポート
   */
  importPlayers: async (teamId, file) => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const { data } = await api.post<Player[]>(
        `/teams/${teamId}/players/import`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      )

      set((state) => ({
        selectedTeam: state.selectedTeam?.id === teamId
          ? {
              ...state.selectedTeam,
              players: [...state.selectedTeam.players, ...data],
            }
          : state.selectedTeam,
      }))

      toast.success(`${data.length}名の選手をインポートしました`)
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '選手のインポートに失敗しました'
      toast.error(message)
      return false
    }
  },

  /**
   * グループ別にチームを取得
   */
  getTeamsByGroup: (groupId) => {
    return get().teams.filter((t) => t.groupId === groupId)
  },

  /**
   * エラーのクリア
   */
  clearError: () => {
    set({ error: null })
  },
}))
