import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/core/http'
import type {
  Tournament,
  Team,
  Match,
  Standing,
  ApiResponse,
} from '@shared/types'

/**
 * 大会一覧取得
 */
export function useTournaments() {
  return useQuery({
    queryKey: ['tournaments'],
    queryFn: async () => {
      const { data } = await api.get<Tournament[]>('/tournaments')
      return data
    },
  })
}

/**
 * 大会詳細取得
 */
export function useTournament(id: number) {
  return useQuery({
    queryKey: ['tournament', id],
    queryFn: async () => {
      const { data } = await api.get<Tournament>(`/tournaments/${id}`)
      return data
    },
    enabled: !!id,
  })
}

/**
 * チーム一覧取得
 */
export function useTeams(tournamentId: number) {
  return useQuery({
    queryKey: ['teams', tournamentId],
    queryFn: async () => {
      const { data } = await api.get<Team[]>(
        `/tournaments/${tournamentId}/teams`
      )
      return data
    },
    enabled: !!tournamentId,
  })
}

/**
 * 試合一覧取得
 */
export function useMatches(
  tournamentId: number,
  options?: { date?: string; venueId?: number }
) {
  return useQuery({
    queryKey: ['matches', tournamentId, options],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (options?.date) params.append('date', options.date)
      if (options?.venueId) params.append('venue_id', options.venueId.toString())

      const { data } = await api.get<Match[]>(
        `/tournaments/${tournamentId}/matches?${params}`
      )
      return data
    },
    enabled: !!tournamentId,
  })
}

/**
 * 順位表取得
 */
export function useStandings(tournamentId: number, groupId?: string) {
  return useQuery({
    queryKey: ['standings', tournamentId, groupId],
    queryFn: async () => {
      const url = groupId
        ? `/tournaments/${tournamentId}/standings/${groupId}`
        : `/tournaments/${tournamentId}/standings`
      const { data } = await api.get<Standing[]>(url)
      return data
    },
    enabled: !!tournamentId,
  })
}

/**
 * 試合結果更新
 */
export function useUpdateMatchScore() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      matchId,
      score,
    }: {
      matchId: number
      score: {
        homeScoreHalf1: number
        homeScoreHalf2: number
        awayScoreHalf1: number
        awayScoreHalf2: number
        homePK?: number
        awayPK?: number
      }
    }) => {
      const { data } = await api.put<ApiResponse<Match>>(
        `/matches/${matchId}/score`,
        score
      )
      return data
    },
    onSuccess: () => {
      // 関連するクエリを無効化して再取得
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      queryClient.invalidateQueries({ queryKey: ['standings'] })
    },
  })
}

/**
 * チーム作成
 */
export function useCreateTeam() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      tournamentId,
      team,
    }: {
      tournamentId: number
      team: Omit<Team, 'id' | 'tournamentId' | 'createdAt' | 'updatedAt'>
    }) => {
      const { data } = await api.post<ApiResponse<Team>>(
        `/tournaments/${tournamentId}/teams`,
        team
      )
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['teams', variables.tournamentId],
      })
    },
  })
}
