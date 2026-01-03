// src/features/venues/hooks.ts
// 会場管理 React Query hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { venueApi } from './api';
import type {
  CreateVenueInput,
  UpdateVenueInput,
  AssignVenueStaffInput,
} from './types';

const QUERY_KEY = ['venues'];

export function useVenuesByTournament(tournamentId: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, { tournamentId }],
    queryFn: () => venueApi.getByTournament(tournamentId),
    enabled: !!tournamentId,
  });
}

export function useVenue(id: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, id],
    queryFn: () => venueApi.getById(id),
    enabled: !!id,
  });
}

export function useVenueStaff(venueId: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, venueId, 'staff'],
    queryFn: () => venueApi.getStaff(venueId),
    enabled: !!venueId,
  });
}

export function useVenueSchedule(venueId: number, date: string) {
  return useQuery({
    queryKey: [...QUERY_KEY, venueId, 'schedule', date],
    queryFn: () => venueApi.getSchedule(venueId, date),
    enabled: !!venueId && !!date,
  });
}

export function useCreateVenue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateVenueInput) => venueApi.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...QUERY_KEY, { tournamentId: variables.tournamentId }],
      });
    },
  });
}

export function useUpdateVenue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateVenueInput) => venueApi.update(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useDeleteVenue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => venueApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useAssignVenueStaff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AssignVenueStaffInput) => venueApi.assignStaff(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...QUERY_KEY, variables.venueId, 'staff'],
      });
    },
  });
}

export function useRemoveVenueStaff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ venueId, userId }: { venueId: number; userId: number }) =>
      venueApi.removeStaff(venueId, userId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...QUERY_KEY, variables.venueId, 'staff'],
      });
    },
  });
}

export function useAssignVenueToGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ venueId, groupId }: { venueId: number; groupId: string }) =>
      venueApi.assignToGroup(venueId, groupId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, variables.venueId] });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}
