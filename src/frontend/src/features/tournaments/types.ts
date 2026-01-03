// src/features/tournaments/types.ts
// 大会管理型定義

export interface Tournament {
  id: number;
  name: string;
  startDate: string;
  endDate: string;
  status: TournamentStatus;
  matchDuration: number; // 試合時間（分）
  intervalMinutes: number; // インターバル（分）
  groupCount: number;
  teamsPerGroup: number;
  description: string | null;
  createdAt: string;
  updatedAt: string;
  version: number;
}

export type TournamentStatus = 'draft' | 'active' | 'completed';

export interface CreateTournamentInput {
  name: string;
  shortName?: string;
  edition: number;
  year: number;
  startDate: string;
  endDate: string;
  matchDuration?: number;
  halfDuration?: number;
  intervalMinutes?: number;
}

export interface UpdateTournamentInput {
  id: number;
  name?: string;
  startDate?: string;
  endDate?: string;
  status?: TournamentStatus;
  matchDuration?: number;
  intervalMinutes?: number;
  description?: string;
  version: number;
}

export interface TournamentGroup {
  id: string;
  tournamentId: number;
  name: string;
  venueId: number | null;
  teamCount: number;
}

export interface TournamentSettings {
  tournamentId: number;
  matchDuration: number;
  intervalMinutes: number;
  halfTimeMinutes: number;
  preliminaryRounds: number;
  tiebreaker: TiebreakerRule[];
}

export type TiebreakerRule =
  | 'points'
  | 'goal_difference'
  | 'goals_scored'
  | 'head_to_head'
  | 'lottery';

export interface GenerateScheduleInput {
  tournamentId: number;
  startTime: string;
  matchesPerDay: number;
}

export interface GenerateFinalScheduleInput {
  tournamentId: number;
  finalDate: string;
  format: 'tournament' | 'ranking_league';
}
