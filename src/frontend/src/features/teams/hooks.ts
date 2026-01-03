// src/features/teams/hooks.ts
// チーム React Query hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teamApi } from './api';
import type { CreateTeamInput, UpdateTeamInput } from './types';

const QUERY_KEY = ['teams'];

export function useTeams(tournamentId?: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, { tournamentId }],
    queryFn: () => teamApi.getAll(tournamentId),
  });
}

export function useTeamsByGroup(tournamentId: number, groupId: string) {
  return useQuery({
    queryKey: [...QUERY_KEY, { tournamentId, groupId }],
    queryFn: () => teamApi.getByGroup(tournamentId, groupId),
    enabled: !!tournamentId && !!groupId,
  });
}

export function useTeam(id: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, id],
    queryFn: () => teamApi.getById(id),
    enabled: id > 0,
  });
}

export function useCreateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTeamInput) => teamApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useUpdateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTeamInput }) =>
      teamApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useDeleteTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => teamApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useImportTeamsCsv() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tournamentId, file }: { tournamentId: number; file: File }) =>
      teamApi.importCsv(tournamentId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}
