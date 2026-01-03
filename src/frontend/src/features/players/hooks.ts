// src/features/players/hooks.ts
// 選手 React Query hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { playerApi } from './api';
import type { CreatePlayerInput, UpdatePlayerInput } from './types';

const QUERY_KEY = ['players'];

export function usePlayersByTeam(teamId: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, { teamId }],
    queryFn: () => playerApi.getByTeam(teamId),
    enabled: teamId > 0,
  });
}

export function usePlayer(id: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, id],
    queryFn: () => playerApi.getById(id),
    enabled: id > 0,
  });
}

export function useCreatePlayer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePlayerInput) => playerApi.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, { teamId: variables.teamId }] });
    },
  });
}

export function useUpdatePlayer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdatePlayerInput }) =>
      playerApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useDeletePlayer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => playerApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function usePlayerSuggestions(teamId: number, query: string) {
  return useQuery({
    queryKey: [...QUERY_KEY, 'suggest', teamId, query],
    queryFn: () => playerApi.suggest(teamId, query),
    enabled: teamId > 0 && query.length >= 1,
    staleTime: 30000, // 30秒間キャッシュ
  });
}

// CSVインポート
export function useImportPlayersCsv() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId, file, replaceExisting }: {
      teamId: number;
      file: File;
      replaceExisting?: boolean;
    }) => playerApi.importCsv(teamId, file, replaceExisting),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, { teamId: variables.teamId }] });
    },
  });
}

// CSVエクスポート
export function useExportPlayersCsv() {
  return useMutation({
    mutationFn: (teamId: number) => playerApi.exportCsv(teamId),
  });
}

// Excelインポートプレビュー
export function usePreviewExcelImport() {
  return useMutation({
    mutationFn: ({ teamId, file }: { teamId: number; file: File }) =>
      playerApi.previewExcelImport(teamId, file),
  });
}

// Excelインポート実行
export function useImportExcel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId, file, options }: {
      teamId: number;
      file: File;
      options?: {
        replaceExisting?: boolean;
        importStaff?: boolean;
        importUniforms?: boolean;
        skipWarnings?: boolean;
      };
    }) => playerApi.importExcel(teamId, file, options),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, { teamId: variables.teamId }] });
      // スタッフとユニフォームも更新
      queryClient.invalidateQueries({ queryKey: ['staff', { teamId: variables.teamId }] });
      queryClient.invalidateQueries({ queryKey: ['uniforms', { teamId: variables.teamId }] });
    },
  });
}
