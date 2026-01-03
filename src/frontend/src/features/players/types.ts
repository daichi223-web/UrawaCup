// src/features/players/types.ts
// 選手型定義

export interface Player {
  id: number;
  teamId: number;
  number: number | null;
  name: string;
  nameKana: string | null;
  nameNormalized: string | null;
  grade: number | null;
  position: 'GK' | 'DF' | 'MF' | 'FW' | null;
  height: number | null;
  previousTeam: string | null;
  isCaptain: boolean;
  isActive: boolean;
  notes: string | null;
  createdAt: string;
  updatedAt: string;

  // 結合データ
  team?: {
    id: number;
    name: string;
  };

  // 集計値（オプション）
  goalCount?: number;
}

export interface CreatePlayerInput {
  teamId: number;
  number?: number | null;
  name: string;
  nameKana?: string;
  grade?: number;
  position?: 'GK' | 'DF' | 'MF' | 'FW';
  height?: number;
  previousTeam?: string;
  isCaptain?: boolean;
  notes?: string;
}

export interface UpdatePlayerInput {
  number?: number | null;
  name?: string;
  nameKana?: string;
  grade?: number;
  position?: 'GK' | 'DF' | 'MF' | 'FW';
  height?: number;
  previousTeam?: string;
  isCaptain?: boolean;
  isActive?: boolean;
  notes?: string;
}

export interface PlayerSuggestion {
  id: number;
  teamId: number;
  number: number | null;
  name: string;
  nameKana: string | null;
  position: string | null;
  grade: number | null;
  displayText: string;
}

// Excel/CSVインポート関連
export interface PlayerImportRow {
  rowNumber: number;
  number: number | null;
  name: string;
  nameKana: string | null;
  grade: number | null;
  position: string | null;
  height: number | null;
  previousTeam: string | null;
  status: 'new' | 'update' | 'error' | 'warning';
  errors: string[];
}

export interface StaffImportRow {
  role: string;
  name: string;
  phone: string | null;
  email: string | null;
}

export interface UniformImportRow {
  playerType: 'GK' | 'FP';
  uniformType: 'primary' | 'secondary';
  shirtColor: string | null;
  pantsColor: string | null;
  socksColor: string | null;
}

export interface ImportError {
  row: number;
  field: string;
  type: 'error' | 'warning';
  message: string;
}

export interface ImportPreviewResult {
  format: string;
  teamInfo: {
    name: string | null;
    address: string | null;
    tel: string | null;
    fax: string | null;
  } | null;
  staff: StaffImportRow[];
  uniforms: UniformImportRow[];
  players: PlayerImportRow[];
  errors: ImportError[];
}

export interface ImportResult {
  imported: number;
  updated: number;
  skipped: number;
  errors: ImportError[];
}
