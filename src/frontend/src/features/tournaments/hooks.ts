// src/features/tournaments/hooks.ts
// 大会管理 React Query hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tournamentApi } from './api';
import type {
  CreateTournamentInput,
  UpdateTournamentInput,
  TournamentSettings,
  GenerateScheduleInput,
  GenerateFinalScheduleInput,
  TournamentStatus,
} from './types';

const QUERY_KEY = ['tournaments'];

export function useTournaments() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: tournamentApi.getAll,
  });
}

export function useTournament(id: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, id],
    queryFn: () => tournamentApi.getById(id),
    enabled: !!id,
  });
}

export function useTournamentGroups(tournamentId: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, tournamentId, 'groups'],
    queryFn: () => tournamentApi.getGroups(tournamentId),
    enabled: !!tournamentId,
  });
}

export function useTournamentSettings(tournamentId: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, tournamentId, 'settings'],
    queryFn: () => tournamentApi.getSettings(tournamentId),
    enabled: !!tournamentId,
  });
}

export function useCreateTournament() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTournamentInput) => tournamentApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useUpdateTournament() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateTournamentInput) => tournamentApi.update(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useDeleteTournament() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => tournamentApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useUpdateTournamentSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tournamentId,
      settings,
    }: {
      tournamentId: number;
      settings: Partial<TournamentSettings>;
    }) => tournamentApi.updateSettings(tournamentId, settings),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...QUERY_KEY, variables.tournamentId, 'settings'],
      });
    },
  });
}

export function useGenerateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GenerateScheduleInput) =>
      tournamentApi.generateSchedule(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['matches', { tournamentId: variables.tournamentId }],
      });
    },
  });
}

export function useGenerateFinalSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GenerateFinalScheduleInput) =>
      tournamentApi.generateFinalSchedule(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['matches', { tournamentId: variables.tournamentId }],
      });
    },
  });
}

export function useChangeTournamentStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: TournamentStatus }) =>
      tournamentApi.changeStatus(id, status),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}
