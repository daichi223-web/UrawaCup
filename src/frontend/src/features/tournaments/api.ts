// src/features/tournaments/api.ts
// 大会管理API呼び出し
import { httpClient } from '@/core/http';
import type {
  Tournament,
  CreateTournamentInput,
  UpdateTournamentInput,
  TournamentGroup,
  TournamentSettings,
  GenerateScheduleInput,
  GenerateFinalScheduleInput,
} from './types';

export const tournamentApi = {
  // 大会一覧取得
  getAll: async (): Promise<Tournament[]> => {
    const response = await httpClient.get<Tournament[]>('/tournaments');
    return response.data;
  },

  // 大会詳細取得
  getById: async (id: number): Promise<Tournament> => {
    const response = await httpClient.get<Tournament>(`/tournaments/${id}`);
    return response.data;
  },

  // 大会作成
  create: async (data: CreateTournamentInput): Promise<Tournament> => {
    const response = await httpClient.post<Tournament>('/tournaments', data);
    return response.data;
  },

  // 大会更新
  update: async (data: UpdateTournamentInput): Promise<Tournament> => {
    const { id, ...rest } = data;
    const response = await httpClient.put<Tournament>(`/tournaments/${id}`, rest);
    return response.data;
  },

  // 大会削除
  delete: async (id: number): Promise<void> => {
    await httpClient.delete(`/tournaments/${id}`);
  },

  // グループ一覧取得
  getGroups: async (tournamentId: number): Promise<TournamentGroup[]> => {
    const response = await httpClient.get<TournamentGroup[]>(
      `/tournaments/${tournamentId}/groups`
    );
    return response.data;
  },

  // 設定取得
  getSettings: async (tournamentId: number): Promise<TournamentSettings> => {
    const response = await httpClient.get<TournamentSettings>(
      `/tournaments/${tournamentId}/settings`
    );
    return response.data;
  },

  // 設定更新
  updateSettings: async (
    tournamentId: number,
    settings: Partial<TournamentSettings>
  ): Promise<TournamentSettings> => {
    const response = await httpClient.put<TournamentSettings>(
      `/tournaments/${tournamentId}/settings`,
      settings
    );
    return response.data;
  },

  // 予選日程生成
  generateSchedule: async (
    data: GenerateScheduleInput
  ): Promise<{ matchCount: number }> => {
    const response = await httpClient.post<{ matchCount: number }>(
      `/tournaments/${data.tournamentId}/generate-schedule`,
      data
    );
    return response.data;
  },

  // 決勝日程生成
  generateFinalSchedule: async (
    data: GenerateFinalScheduleInput
  ): Promise<{ matchCount: number }> => {
    const response = await httpClient.post<{ matchCount: number }>(
      `/tournaments/${data.tournamentId}/generate-final-schedule`,
      data
    );
    return response.data;
  },

  // 大会ステータス変更
  changeStatus: async (
    id: number,
    status: Tournament['status']
  ): Promise<Tournament> => {
    const response = await httpClient.patch<Tournament>(
      `/tournaments/${id}/status`,
      { status }
    );
    return response.data;
  },
};
