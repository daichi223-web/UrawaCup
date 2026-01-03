// src/features/final-day/api.ts
// 最終日組み合わせAPI呼び出し

import { httpClient } from '@/core/http';
import type { MatchWithDetails } from '@shared/types';
import type { SwapTeamsRequest } from './types';

interface MatchListResponse {
  matches: MatchWithDetails[];
  total: number;
}

export const finalDayApi = {
  /**
   * 決勝トーナメント試合一覧を取得
   */
  getFinalMatches: async (tournamentId: number): Promise<MatchWithDetails[]> => {
    const response = await httpClient.get<MatchListResponse>(
      `/matches/finals/${tournamentId}`
    );
    return response.data.matches;
  },

  /**
   * 研修試合一覧を取得
   */
  getTrainingMatches: async (tournamentId: number, matchDate?: string): Promise<MatchWithDetails[]> => {
    const response = await httpClient.get<MatchListResponse>('/matches', {
      params: {
        tournament_id: tournamentId,
        stage: 'training',
        match_date: matchDate,
      },
    });
    return response.data.matches;
  },

  /**
   * 最終日（Day3）の全試合を取得
   */
  getFinalDayMatches: async (tournamentId: number, matchDate: string): Promise<MatchWithDetails[]> => {
    const response = await httpClient.get<MatchListResponse>('/matches', {
      params: {
        tournament_id: tournamentId,
        match_date: matchDate,
      },
    });
    return response.data.matches;
  },

  /**
   * 決勝トーナメントを自動生成
   */
  generateFinals: async (
    tournamentId: number,
    matchDate: string,
    startTime: string = '09:00',
    venueId?: number
  ): Promise<MatchWithDetails[]> => {
    const params: Record<string, unknown> = {
      match_date: matchDate,
      start_time: startTime,
    };
    if (venueId) {
      params.venue_id = venueId;
    }
    const response = await httpClient.post<MatchListResponse>(
      `/matches/generate-finals/${tournamentId}`,
      null,
      { params }
    );
    return response.data.matches;
  },

  /**
   * 研修試合を自動生成
   */
  generateTrainingMatches: async (
    tournamentId: number,
    matchDate: string,
    startTime: string = '09:30',
    minVenues: number = 1
  ): Promise<MatchWithDetails[]> => {
    const response = await httpClient.post<MatchListResponse>(
      `/matches/generate-training/${tournamentId}`,
      null,
      {
        params: {
          match_date: matchDate,
          start_time: startTime,
          min_venues: minVenues,
        },
      }
    );
    return response.data.matches;
  },

  /**
   * 準決勝結果に基づいて決勝・3位決定戦のチームを更新
   */
  updateFinalsBracket: async (tournamentId: number): Promise<void> => {
    await httpClient.put(`/matches/update-finals-bracket/${tournamentId}`);
  },

  /**
   * 試合のチームを変更
   */
  updateMatchTeams: async (
    matchId: number,
    homeTeamId: number,
    awayTeamId: number
  ): Promise<MatchWithDetails> => {
    const response = await httpClient.put<MatchWithDetails>(
      `/matches/finals/${matchId}/teams`,
      null,
      {
        params: {
          home_team_id: homeTeamId,
          away_team_id: awayTeamId,
        },
      }
    );
    return response.data;
  },

  /**
   * 2試合間でチームを入れ替える
   */
  swapTeams: async (request: SwapTeamsRequest): Promise<{
    match1: MatchWithDetails;
    match2: MatchWithDetails;
  }> => {
    const response = await httpClient.post<{
      match1: MatchWithDetails;
      match2: MatchWithDetails;
    }>('/matches/swap-teams', request);
    return response.data;
  },

  /**
   * 試合を削除
   */
  deleteMatch: async (matchId: number): Promise<void> => {
    await httpClient.delete(`/matches/${matchId}`);
  },

  /**
   * 2チームが予選で対戦済みかチェック
   */
  checkPlayed: async (
    tournamentId: number,
    team1Id: number,
    team2Id: number
  ): Promise<{
    played: boolean;
    matchId: number | null;
    matchDate: string | null;
    homeScore: number | null;
    awayScore: number | null;
    message: string;
  }> => {
    const response = await httpClient.get<{
      played: boolean;
      match_id: number | null;
      match_date: string | null;
      home_score: number | null;
      away_score: number | null;
      message: string;
    }>('/matches/check-played', {
      params: {
        tournament_id: tournamentId,
        team1_id: team1Id,
        team2_id: team2Id,
      },
    });
    return {
      played: response.data.played,
      matchId: response.data.match_id,
      matchDate: response.data.match_date,
      homeScore: response.data.home_score,
      awayScore: response.data.away_score,
      message: response.data.message,
    };
  },
};
