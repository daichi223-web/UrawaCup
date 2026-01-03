// src/features/staff/hooks.ts
// スタッフ React Query hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { staffApi } from './api';
import type { CreateStaffInput, UpdateStaffInput } from './types';

const QUERY_KEY = ['staff'];

export function useStaffByTeam(teamId: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, { teamId }],
    queryFn: () => staffApi.getByTeam(teamId),
    enabled: teamId > 0,
  });
}

export function useStaff(id: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, id],
    queryFn: () => staffApi.getById(id),
    enabled: id > 0,
  });
}

export function useCreateStaff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateStaffInput) => staffApi.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, { teamId: variables.teamId }] });
    },
  });
}

export function useUpdateStaff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateStaffInput }) =>
      staffApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useDeleteStaff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => staffApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}
