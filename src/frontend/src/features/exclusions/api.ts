// src/features/exclusions/api.ts
// 対戦除外設定API呼び出し
import { httpClient } from '@/core/http';
import type {
  ExclusionPair,
  CreateExclusionInput,
  ExclusionSuggestion,
  BulkExclusionInput,
} from './types';

// 後方互換のため@shared/typesからの型もインポート
import type { GroupExclusions, ExclusionPairCreate } from '@shared/types';

export const exclusionApi = {
  // グループの除外ペア一覧
  getByGroup: async (tournamentId: number, groupId: string): Promise<ExclusionPair[]> => {
    const response = await httpClient.get<ExclusionPair[]>('/exclusions', {
      params: { tournamentId, groupId },
    });
    return response.data;
  },

  // 後方互換: グループ別除外設定一覧取得
  getExclusionsByGroup: async (tournamentId: number): Promise<GroupExclusions[]> => {
    const response = await httpClient.get<GroupExclusions[]>('/exclusions/by-group', {
      params: { tournamentId },
    });
    return response.data;
  },

  // 除外ペア作成
  create: async (data: CreateExclusionInput): Promise<ExclusionPair> => {
    const response = await httpClient.post<ExclusionPair>('/exclusions', data);
    return response.data;
  },

  // 後方互換: 除外設定追加
  createExclusion: async (data: ExclusionPairCreate): Promise<ExclusionPair> => {
    const response = await httpClient.post<ExclusionPair>('/exclusions/', data);
    return response.data;
  },

  // 除外ペア削除
  delete: async (id: number): Promise<void> => {
    await httpClient.delete(`/exclusions/${id}`);
  },

  // 後方互換: 除外設定削除
  deleteExclusion: async (id: number): Promise<void> => {
    await httpClient.delete(`/exclusions/${id}`);
  },

  // 一括登録
  bulkCreate: async (data: BulkExclusionInput): Promise<{ created: number }> => {
    const response = await httpClient.post<{ created: number }>('/exclusions/bulk', data);
    return response.data;
  },

  // 自動提案取得
  getSuggestions: async (tournamentId: number, groupId: string): Promise<ExclusionSuggestion[]> => {
    const response = await httpClient.post<ExclusionSuggestion[]>('/exclusions/auto-suggest', {
      tournamentId,
      groupId,
    });
    return response.data;
  },

  // グループの除外ペアをクリア
  clearGroup: async (tournamentId: number, groupId: string): Promise<void> => {
    await httpClient.delete('/exclusions/clear', {
      params: { tournamentId, groupId },
    });
  },
};
