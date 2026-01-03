// src/features/standings/api.ts
// 順位表API呼び出し
import { httpClient } from '@/core/http';
import type { GroupStandings, TopScorer, ResolveTiebreakerInput } from './types';

// バックエンドのレスポンス型
interface BackendGroupStanding {
  group: {
    id: string;
    name: string;
    venueId?: number;
    tournamentId: number;
  };
  standings: GroupStandings['standings'];
}

// バックエンドレスポンスをフロントエンド形式に変換
function transformGroupStanding(backend: BackendGroupStanding): GroupStandings {
  return {
    groupId: backend.group.id,
    standings: backend.standings,
    needsTiebreaker: false, // バックエンドで計算される場合は追加
  };
}

export const standingApi = {
  // グループ別順位表取得
  getByGroup: async (tournamentId: number, groupId: string): Promise<GroupStandings> => {
    const response = await httpClient.get<BackendGroupStanding[]>('/standings/by-group', {
      params: { tournamentId },
    });
    const found = response.data.find(g => g.group.id === groupId);
    if (!found) {
      return { groupId, standings: [], needsTiebreaker: false };
    }
    return transformGroupStanding(found);
  },

  // 後方互換: グループ別順位表取得
  getStandingsByGroup: async (tournamentId: number): Promise<GroupStandings[]> => {
    const response = await httpClient.get<BackendGroupStanding[]>('/standings/by-group', {
      params: { tournamentId },
    });
    return response.data.map(transformGroupStanding);
  },

  // 全グループ順位表取得
  getAll: async (tournamentId: number): Promise<GroupStandings[]> => {
    const response = await httpClient.get<BackendGroupStanding[]>('/standings/by-group', {
      params: { tournamentId },
    });
    return response.data.map(transformGroupStanding);
  },

  // 順位再計算
  recalculate: async (tournamentId: number, groupId?: string): Promise<void> => {
    await httpClient.post('/standings/recalculate', {
      tournamentId,
      groupId,
    });
  },

  // 抽選結果を登録（タイブレーカー解決）
  resolveTiebreaker: async (data: ResolveTiebreakerInput): Promise<void> => {
    await httpClient.post('/standings/resolve-tiebreaker', data);
  },

  // 得点ランキング取得
  getTopScorers: async (tournamentId: number, limit = 10): Promise<TopScorer[]> => {
    const response = await httpClient.get<TopScorer[]>('/standings/top-scorers', {
      params: { tournamentId, limit },
    });
    return response.data;
  },
};
