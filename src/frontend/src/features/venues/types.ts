// src/features/venues/types.ts
// 会場管理型定義

export interface Venue {
  id: number;
  tournamentId: number;
  name: string;
  shortName: string;
  address: string | null;
  pitchCount: number; // コート数
  hostTeamId: number | null; // 会場担当チーム
  groupId: string | null;
  forFinalDay: boolean; // 最終日の順位リーグ会場
  isFinalsVenue: boolean; // 決勝トーナメント会場
  createdAt: string;
  updatedAt: string;

  // snake_case aliases (from API response)
  group_id?: string;
  for_final_day?: boolean;
  is_finals_venue?: boolean;
  max_matches_per_day?: number;
  maxMatchesPerDay?: number;

  // 結合データ
  hostTeam?: { id: number; name: string };
}

export interface CreateVenueInput {
  tournamentId: number;
  name: string;
  shortName: string;
  address?: string;
  pitchCount?: number;
  hostTeamId?: number;
  groupId?: string;
  forFinalDay?: boolean;
  isFinalsVenue?: boolean;
}

export interface UpdateVenueInput {
  id: number;
  name?: string;
  shortName?: string;
  address?: string;
  pitchCount?: number;
  hostTeamId?: number;
  groupId?: string;
  group_id?: string;
  max_matches_per_day?: number;
  for_final_day?: boolean;
  is_finals_venue?: boolean;
}

export interface VenueStaff {
  id: number;
  venueId: number;
  userId: number;
  role: 'manager' | 'staff';
  createdAt: string;

  // 結合データ
  user?: { id: number; username: string; name: string };
}

export interface AssignVenueStaffInput {
  venueId: number;
  userId: number;
  role: 'manager' | 'staff';
}

export interface VenueSchedule {
  venueId: number;
  date: string;
  matches: {
    id: number;
    startTime: string;
    endTime: string;
    homeTeam: string;
    awayTeam: string;
    status: string;
  }[];
}
