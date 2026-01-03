// src/features/teams/api.ts
// チームAPI呼び出し
import { httpClient } from '@/core/http';
import type { Team, CreateTeamInput, UpdateTeamInput, TeamWithPlayers } from './types';

interface TeamListResponse {
  teams: Team[];
  total: number;
}

export const teamApi = {
  // 全チーム取得
  getAll: async (tournamentId?: number): Promise<Team[]> => {
    const params = tournamentId ? { tournamentId } : undefined;
    const response = await httpClient.get<TeamListResponse>('/teams', { params });
    return response.data.teams || [];
  },

  // グループ別チーム取得
  getByGroup: async (tournamentId: number, groupId: string): Promise<Team[]> => {
    const response = await httpClient.get<TeamListResponse>('/teams', {
      params: { tournamentId, groupId },
    });
    return response.data.teams || [];
  },

  // 単一チーム取得
  getById: async (id: number): Promise<TeamWithPlayers> => {
    const response = await httpClient.get<TeamWithPlayers>(`/teams/${id}`);
    return response.data;
  },

  // チーム作成
  create: async (data: CreateTeamInput): Promise<Team> => {
    const response = await httpClient.post<Team>('/teams', data);
    return response.data;
  },

  // チーム更新
  update: async (id: number, data: UpdateTeamInput): Promise<Team> => {
    const response = await httpClient.patch<Team>(`/teams/${id}`, data);
    return response.data;
  },

  // チーム削除
  delete: async (id: number): Promise<void> => {
    await httpClient.delete(`/teams/${id}`);
  },

  // CSVインポート
  importCsv: async (tournamentId: number, file: File): Promise<{ imported: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tournamentId', String(tournamentId));

    const response = await httpClient.post<{ imported: number }>(
      '/teams/import-csv',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  // CSVエクスポート
  exportCsv: async (tournamentId: number): Promise<Blob> => {
    const response = await httpClient.get('/teams/export-csv', {
      params: { tournamentId },
      responseType: 'blob',
    });
    return response.data;
  },
};
