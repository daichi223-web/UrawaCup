// src/features/matches/api.ts
// 試合API呼び出し
import { httpClient } from '@/core/http';
import type {
  Match,
  MatchScoreInput,
  CreateMatchInput,
  MatchGenerateScheduleInput,
  MatchStage,
  MatchLock,
} from './types';

// 後方互換のため@shared/typesからもインポート
import type { MatchWithDetails } from '@shared/types';

export const matchApi = {
  // 試合一覧取得
  getAll: async (params?: {
    tournamentId?: number;
    groupId?: string;
    venueId?: number;
    matchDate?: string;
    stage?: MatchStage;
  }): Promise<Match[]> => {
    const response = await httpClient.get<Match[]>('/matches', { params });
    return response.data;
  },

  // 後方互換: 試合一覧取得
  getMatches: async (params?: Record<string, unknown>): Promise<{ matches: MatchWithDetails[], total: number }> => {
    const response = await httpClient.get<{ matches: MatchWithDetails[], total: number }>('/matches', { params });
    return response.data;
  },

  // 単一試合取得
  getById: async (id: number): Promise<Match> => {
    const response = await httpClient.get<Match>(`/matches/${id}`);
    return response.data;
  },

  // 後方互換: 単一試合取得
  getMatch: async (id: number): Promise<MatchWithDetails> => {
    const response = await httpClient.get<MatchWithDetails>(`/matches/${id}`);
    return response.data;
  },

  // 試合作成
  create: async (data: CreateMatchInput): Promise<Match> => {
    const response = await httpClient.post<Match>('/matches', data);
    return response.data;
  },

  // スコア入力
  updateScore: async (id: number, data: MatchScoreInput): Promise<Match> => {
    const response = await httpClient.put<Match>(`/matches/${id}/score`, data);
    return response.data;
  },

  // 試合削除
  delete: async (id: number): Promise<void> => {
    await httpClient.delete(`/matches/${id}`);
  },

  // 日程自動生成（予選リーグ）
  generateSchedule: async (data: MatchGenerateScheduleInput): Promise<{ created: number }> => {
    const response = await httpClient.post<{ created: number }>(
      '/matches/generate-schedule',
      data
    );
    return response.data;
  },

  // 研修試合生成
  generateTrainingMatches: async (tournamentId: number): Promise<{ created: number }> => {
    const response = await httpClient.post<{ created: number }>(
      '/matches/generate-training',
      { tournamentId }
    );
    return response.data;
  },

  // 決勝トーナメント生成
  generateFinals: async (tournamentId: number): Promise<{ created: number }> => {
    const response = await httpClient.post<{ created: number }>(
      '/matches/generate-finals',
      { tournamentId }
    );
    return response.data;
  },

  // 承認
  approve: async (id: number): Promise<Match> => {
    const response = await httpClient.post<Match>(`/matches/${id}/approve`);
    return response.data;
  },

  // 後方互換: 承認
  approveMatch: async (id: number): Promise<Match> => {
    const response = await httpClient.post<Match>(`/matches/${id}/approve`);
    return response.data;
  },

  // 却下
  reject: async (id: number, reason: string): Promise<Match> => {
    const response = await httpClient.post<Match>(`/matches/${id}/reject`, { reason });
    return response.data;
  },

  // 後方互換: 却下
  rejectMatch: async (id: number, reason: string): Promise<Match> => {
    const response = await httpClient.post<Match>(`/matches/${id}/reject`, { reason });
    return response.data;
  },

  // ロック取得
  lock: async (id: number): Promise<MatchLock> => {
    const response = await httpClient.post<MatchLock>(`/matches/${id}/lock`);
    return response.data;
  },

  // ロック解除
  unlock: async (id: number, force?: boolean): Promise<MatchLock> => {
    const response = await httpClient.post<MatchLock>(`/matches/${id}/unlock`, null, {
      params: force ? { force: true } : undefined,
    });
    return response.data;
  },

  // 承認待ち一覧
  getPendingApproval: async (tournamentId: number): Promise<Match[]> => {
    const response = await httpClient.get<Match[]>('/matches/pending-approval', {
      params: { tournamentId },
    });
    return response.data;
  },
};
