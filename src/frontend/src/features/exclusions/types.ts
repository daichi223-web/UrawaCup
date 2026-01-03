// src/features/exclusions/types.ts
// 対戦除外設定型定義

export interface ExclusionPair {
  id: number;
  tournamentId: number;
  groupId: string;
  team1Id: number;
  team2Id: number;
  reason: string | null;
  createdAt: string;

  // 結合データ
  team1?: { id: number; name: string };
  team2?: { id: number; name: string };
}

export interface CreateExclusionInput {
  tournamentId: number;
  groupId: string;
  team1Id: number;
  team2Id: number;
  reason?: string;
}

export interface ExclusionSuggestion {
  team1Id: number;
  team1Name: string;
  team2Id: number;
  team2Name: string;
  suggestedReason: string;
}

export interface BulkExclusionInput {
  tournamentId: number;
  groupId: string;
  pairs: {
    team1Id: number;
    team2Id: number;
    reason?: string;
  }[];
}
