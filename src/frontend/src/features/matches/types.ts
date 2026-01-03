// src/features/matches/types.ts
// 試合型定義

export type MatchStage =
  | 'preliminary'   // 予選リーグ
  | 'training'      // 研修試合
  | 'semifinal'     // 準決勝
  | 'third_place'   // 3位決定戦
  | 'final';        // 決勝

export type MatchStatus =
  | 'scheduled'     // 予定
  | 'in_progress'   // 進行中
  | 'completed'     // 終了
  | 'cancelled';    // 中止

export type ApprovalStatus =
  | 'pending'       // 承認待ち
  | 'approved'      // 承認済み
  | 'rejected';     // 却下

export interface Match {
  id: number;
  tournamentId: number;
  groupId: string | null;
  venueId: number;
  homeTeamId: number;
  awayTeamId: number;
  matchDate: string;
  matchTime: string;
  matchOrder: number;
  stage: MatchStage;
  status: MatchStatus;
  homeScoreHalf1: number | null;
  homeScoreHalf2: number | null;
  homeScoreTotal: number | null;
  awayScoreHalf1: number | null;
  awayScoreHalf2: number | null;
  awayScoreTotal: number | null;
  homePk: number | null;
  awayPk: number | null;
  hasPenaltyShootout: boolean;
  approvalStatus: ApprovalStatus;
  approvedBy: number | null;
  approvedAt: string | null;
  rejectionReason: string | null;
  version: number;
  createdAt: string;
  updatedAt: string;

  // 結合データ
  homeTeam?: { id: number; name: string; shortName: string };
  awayTeam?: { id: number; name: string; shortName: string };
  venue?: { id: number; name: string };
  goals?: Goal[];
}

export interface Goal {
  id: number;
  matchId: number;
  teamId: number;
  playerId: number | null;
  scorerName: string;
  minute: number;
  half: 1 | 2;
  isOwnGoal: boolean;
}

export interface MatchScoreInput {
  homeScoreHalf1: number;
  homeScoreHalf2: number;
  awayScoreHalf1: number;
  awayScoreHalf2: number;
  homePk?: number;
  awayPk?: number;
  hasPenaltyShootout?: boolean;
  goals?: Omit<Goal, 'id' | 'matchId'>[];
}

export interface CreateMatchInput {
  tournamentId: number;
  groupId?: string;
  venueId: number;
  homeTeamId: number;
  awayTeamId: number;
  matchDate: string;
  matchTime: string;
  matchOrder: number;
  stage: MatchStage;
}

export interface MatchGenerateScheduleInput {
  tournamentId: number;
  groupId: string;
  startDate: string;
  startTime: string;
  interval: number;
  matchesPerDay: number;
}

// ロック情報
export interface MatchLock {
  matchId: number;
  isLocked: boolean;
  lockedBy?: number;
  lockedAt?: string;
}
