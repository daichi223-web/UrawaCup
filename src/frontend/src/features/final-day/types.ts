// src/features/final-day/types.ts
// 最終日組み合わせ画面の型定義

import type { Match, MatchWithDetails, Venue, Team } from '@shared/types';

/** 最終日試合の種別 */
export type FinalMatchType = 'semifinal' | 'final' | 'third_place' | 'training';

/** チームスロットの種別 */
export type TeamSlotType = 'fixed' | 'seed' | 'winner' | 'loser';

/** チームスロット（ドラッグ可能） */
export interface TeamSlot {
  /** スロット種別 */
  type: TeamSlotType;
  /** チームID（type='fixed' の場合） */
  teamId?: number;
  /** チーム名 */
  teamName?: string;
  /** シード表記（例: "A1位", "4位③"） */
  seed?: string;
  /** 表示名 */
  displayName: string;
  /** 参照元試合ID（type='winner'/'loser' の場合） */
  sourceMatchId?: number;
}

/** 最終日試合 */
export interface FinalMatch {
  id: number;
  matchType: FinalMatchType;
  /** ラウンド番号（研修試合用） */
  round?: number;
  /** 会場 */
  venue: {
    id: number;
    name: string;
  };
  /** キックオフ時刻（HH:mm） */
  kickoffTime: string;
  /** 試合日 */
  matchDate: string;
  /** 試合順 */
  matchOrder: number;
  /** ホームチーム */
  homeTeam: TeamSlot;
  /** アウェイチーム */
  awayTeam: TeamSlot;
  /** ホームスコア */
  homeScore?: number;
  /** アウェイスコア */
  awayScore?: number;
  /** ステータス */
  status: 'scheduled' | 'completed';
  /** 審判情報 */
  referee?: {
    main: string;
    assistant: string;
  };
  /** 備考 */
  notes?: string;
}

/** 会場別スケジュール */
export interface VenueSchedule {
  id: number;
  name: string;
  /** 会場担当 */
  manager?: string;
  /** 試合一覧 */
  matches: FinalMatch[];
}

/** 最終日スケジュール全体 */
export interface FinalDaySchedule {
  date: string;
  tournamentId: number;
  /** 順位リーグ（研修試合） */
  trainingLeague: {
    title: string;
    venues: VenueSchedule[];
  };
  /** 決勝トーナメント */
  knockout: {
    title: string;
    venue: string;
    matches: FinalMatch[];
  };
}

/** ドラッグアイテム */
export interface DragItem {
  type: 'team';
  matchId: number;
  side: 'home' | 'away';
  team: TeamSlot;
}

/** ドロップターゲット */
export interface DropTarget {
  matchId: number;
  side: 'home' | 'away';
}

/** チーム入れ替えリクエスト */
export interface SwapTeamsRequest {
  match1Id: number;
  side1: 'home' | 'away';
  match2Id: number;
  side2: 'home' | 'away';
}

/** チーム変更リクエスト */
export interface UpdateMatchTeamsRequest {
  matchId: number;
  homeTeamId: number;
  awayTeamId: number;
}

/** MatchWithDetailsからFinalMatchへの変換用 */
export function toFinalMatch(match: MatchWithDetails): FinalMatch {
  const matchType = match.stage as FinalMatchType;

  return {
    id: match.id,
    matchType,
    venue: {
      id: match.venue?.id ?? match.venueId,
      name: match.venue?.name ?? '',
    },
    kickoffTime: match.matchTime,
    matchDate: match.matchDate,
    matchOrder: match.matchOrder,
    homeTeam: {
      type: 'fixed',
      teamId: match.homeTeam?.id ?? match.homeTeamId,
      teamName: match.homeTeam?.name,
      displayName: match.homeTeam?.name ?? match.homeTeam?.shortName ?? `Team ${match.homeTeamId}`,
    },
    awayTeam: {
      type: 'fixed',
      teamId: match.awayTeam?.id ?? match.awayTeamId,
      teamName: match.awayTeam?.name,
      displayName: match.awayTeam?.name ?? match.awayTeam?.shortName ?? `Team ${match.awayTeamId}`,
    },
    homeScore: match.homeScoreTotal ?? undefined,
    awayScore: match.awayScoreTotal ?? undefined,
    status: match.status === 'completed' ? 'completed' : 'scheduled',
    notes: match.notes ?? undefined,
  };
}

/** シード表記からグループと順位を解析 */
export function parseSeed(seed: string): { group?: string; rank?: number; suffix?: string } | null {
  // "A1" → { group: 'A', rank: 1 }
  const groupMatch = seed.match(/^([A-D])(\d)$/);
  if (groupMatch) {
    return { group: groupMatch[1], rank: parseInt(groupMatch[2]) };
  }

  // "4位③" → { rank: 4, suffix: '③' }
  const rankMatch = seed.match(/^(\d)位([①②③④])$/);
  if (rankMatch) {
    return { rank: parseInt(rankMatch[1]), suffix: rankMatch[2] };
  }

  // "A1位" → { group: 'A', rank: 1 }
  const fullMatch = seed.match(/^([A-D])(\d)位$/);
  if (fullMatch) {
    return { group: fullMatch[1], rank: parseInt(fullMatch[2]) };
  }

  return null;
}
