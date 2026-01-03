// src/features/standings/hooks.ts
// 順位表 React Query hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { standingApi } from './api';
import type { ResolveTiebreakerInput } from './types';

const QUERY_KEY = ['standings'];

export function useGroupStandings(tournamentId: number, groupId: string) {
  return useQuery({
    queryKey: [...QUERY_KEY, { tournamentId, groupId }],
    queryFn: () => standingApi.getByGroup(tournamentId, groupId),
    enabled: !!tournamentId && !!groupId,
  });
}

export function useAllStandings(tournamentId: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, 'all', tournamentId],
    queryFn: () => standingApi.getAll(tournamentId),
    enabled: tournamentId > 0,
  });
}

export function useRecalculateStandings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tournamentId, groupId }: { tournamentId: number; groupId?: string }) =>
      standingApi.recalculate(tournamentId, groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useResolveTiebreaker() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ResolveTiebreakerInput) => standingApi.resolveTiebreaker(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useTopScorers(tournamentId: number, limit = 10) {
  return useQuery({
    queryKey: [...QUERY_KEY, 'top-scorers', tournamentId, limit],
    queryFn: () => standingApi.getTopScorers(tournamentId, limit),
    enabled: tournamentId > 0,
  });
}
