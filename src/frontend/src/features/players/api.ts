// src/features/players/api.ts
// 選手API呼び出し
import { httpClient } from '@/core/http';
import type {
  Player,
  CreatePlayerInput,
  UpdatePlayerInput,
  PlayerSuggestion,
  ImportPreviewResult,
  ImportResult,
} from './types';

interface PlayerListResponse {
  players: Player[];
  total: number;
}

export const playerApi = {
  // チームの選手一覧
  getByTeam: async (teamId: number): Promise<Player[]> => {
    const response = await httpClient.get<PlayerListResponse>('/players', {
      params: { teamId },
    });
    return response.data.players;
  },

  // 単一選手取得
  getById: async (id: number): Promise<Player> => {
    const response = await httpClient.get<Player>(`/players/${id}`);
    return response.data;
  },

  // 選手作成
  create: async (data: CreatePlayerInput): Promise<Player> => {
    const response = await httpClient.post<Player>('/players', data);
    return response.data;
  },

  // 選手更新
  update: async (id: number, data: UpdatePlayerInput): Promise<Player> => {
    const response = await httpClient.put<Player>(`/players/${id}`, data);
    return response.data;
  },

  // 選手削除
  delete: async (id: number): Promise<void> => {
    await httpClient.delete(`/players/${id}`);
  },

  // 選手サジェスト（得点者入力用）
  suggest: async (teamId: number, query: string): Promise<PlayerSuggestion[]> => {
    const response = await httpClient.get<PlayerSuggestion[]>('/players/suggest', {
      params: { teamId, q: query },
    });
    return response.data;
  },

  // CSVインポート
  importCsv: async (
    teamId: number,
    file: File,
    replaceExisting: boolean = false
  ): Promise<PlayerListResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await httpClient.post<PlayerListResponse>(
      `/players/import-csv/${teamId}`,
      formData,
      {
        params: { replace_existing: replaceExisting },
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  // CSVエクスポート
  exportCsv: async (teamId: number): Promise<Blob> => {
    const response = await httpClient.get(`/players/export-csv/${teamId}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Excelインポートプレビュー
  previewExcelImport: async (teamId: number, file: File): Promise<ImportPreviewResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await httpClient.post<ImportPreviewResult>(
      `/players/import-excel/${teamId}/preview`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  // Excelインポート実行
  importExcel: async (
    teamId: number,
    file: File,
    options: {
      replaceExisting?: boolean;
      importStaff?: boolean;
      importUniforms?: boolean;
      skipWarnings?: boolean;
    } = {}
  ): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await httpClient.post<ImportResult>(
      `/players/import-excel/${teamId}`,
      formData,
      {
        params: {
          replace_existing: options.replaceExisting ?? false,
          import_staff: options.importStaff ?? true,
          import_uniforms: options.importUniforms ?? true,
          skip_warnings: options.skipWarnings ?? true,
        },
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },
};
