// src/features/exclusions/hooks.ts
// 対戦除外設定 React Query hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { exclusionApi } from './api';
import type { CreateExclusionInput, BulkExclusionInput } from './types';

const QUERY_KEY = ['exclusions'];

export function useExclusionsByGroup(tournamentId: number, groupId: string) {
  return useQuery({
    queryKey: [...QUERY_KEY, { tournamentId, groupId }],
    queryFn: () => exclusionApi.getByGroup(tournamentId, groupId),
    enabled: !!tournamentId && !!groupId,
  });
}

export function useCreateExclusion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateExclusionInput) => exclusionApi.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...QUERY_KEY, { tournamentId: variables.tournamentId, groupId: variables.groupId }],
      });
    },
  });
}

export function useDeleteExclusion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => exclusionApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useBulkCreateExclusions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BulkExclusionInput) => exclusionApi.bulkCreate(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...QUERY_KEY, { tournamentId: variables.tournamentId, groupId: variables.groupId }],
      });
    },
  });
}

export function useExclusionSuggestions() {
  return useMutation({
    mutationFn: ({ tournamentId, groupId }: { tournamentId: number; groupId: string }) =>
      exclusionApi.getSuggestions(tournamentId, groupId),
  });
}

export function useClearExclusions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tournamentId, groupId }: { tournamentId: number; groupId: string }) =>
      exclusionApi.clearGroup(tournamentId, groupId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...QUERY_KEY, { tournamentId: variables.tournamentId, groupId: variables.groupId }],
      });
    },
  });
}
