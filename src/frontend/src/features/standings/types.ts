// src/features/standings/types.ts
// 順位表型定義 - 共有型を再エクスポートし、API固有の型を追加

// 共有型を再エクスポート
export type {
  Standing,
  StandingWithTeam,
  GroupStanding,
} from '@shared/types';

// API固有の型定義

/** グループ順位表（API応答形式） */
export interface GroupStandings {
  groupId: string;
  standings: Array<{
    id: number;
    tournamentId: number;
    groupId: string;
    teamId: number;
    rank: number;
    played: number;
    won: number;
    drawn: number;
    lost: number;
    goalsFor: number;
    goalsAgainst: number;
    goalDifference: number;
    points: number;
    rankReason: string | null;
    version: number;
    calculatedAt: string;
    team?: {
      id: number;
      name: string;
      shortName: string;
    };
  }>;
  needsTiebreaker: boolean;
  tiedTeams?: { teamId: number; teamName: string }[];
}

/** 得点ランキング */
export interface TopScorer {
  rank: number;
  scorerName: string;
  teamId: number;
  teamName: string;
  goals: number;
}

/** タイブレーカー解決入力 */
export interface ResolveTiebreakerInput {
  tournamentId: number;
  groupId: string;
  rankings: { teamId: number; rank: number }[];
}
