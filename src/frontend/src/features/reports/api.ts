// src/features/reports/api.ts
// 報告書API呼び出し
import { httpClient } from '@/core/http';
import type { ReportGenerateInput, ReportJob, ReportRecipient } from './types';

export const reportApi = {
  // 報告書生成開始
  generate: async (data: ReportGenerateInput): Promise<{ jobId: string }> => {
    const response = await httpClient.post<{ jobId: string }>('/reports/generate', data);
    return response.data;
  },

  // 生成ジョブ状態確認
  getJobStatus: async (jobId: string): Promise<ReportJob> => {
    const response = await httpClient.get<ReportJob>(`/reports/jobs/${jobId}`);
    return response.data;
  },

  // 報告書ダウンロード
  download: async (jobId: string): Promise<Blob> => {
    const response = await httpClient.get(`/reports/download/${jobId}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // 後方互換: PDFダウンロード
  downloadPdf: async (params: { tournamentId: number; date: string; venueId?: number; format?: string }): Promise<Blob> => {
    const response = await httpClient.get('/reports/export/pdf', {
      params: {
        tournamentId: params.tournamentId,
        targetDate: params.date,
        venueId: params.venueId,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // 後方互換: Excelダウンロード
  downloadExcel: async (params: { tournamentId: number; date: string; venueId?: number; format?: string }): Promise<Blob> => {
    const response = await httpClient.get('/reports/export/excel', {
      params: {
        tournamentId: params.tournamentId,
        targetDate: params.date,
        venueId: params.venueId,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // 送信先一覧
  getRecipients: async (tournamentId: number): Promise<ReportRecipient[]> => {
    const response = await httpClient.get<ReportRecipient[]>('/reports/recipients', {
      params: { tournamentId },
    });
    return response.data;
  },

  // 送信先追加
  addRecipient: async (data: Omit<ReportRecipient, 'id'>): Promise<ReportRecipient> => {
    const response = await httpClient.post<ReportRecipient>('/reports/recipients', data);
    return response.data;
  },

  // 送信先更新
  updateRecipient: async (id: number, data: Partial<ReportRecipient>): Promise<ReportRecipient> => {
    const response = await httpClient.patch<ReportRecipient>(`/reports/recipients/${id}`, data);
    return response.data;
  },

  // 送信先削除
  deleteRecipient: async (id: number): Promise<void> => {
    await httpClient.delete(`/reports/recipients/${id}`);
  },

  // 最終日組み合わせ表PDFダウンロード
  downloadFinalDaySchedule: async (params: { tournamentId: number; date: string }): Promise<Blob> => {
    const response = await httpClient.get('/reports/export/final-day-schedule', {
      params: {
        tournament_id: params.tournamentId,
        target_date: params.date,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // 最終結果報告書PDFダウンロード
  downloadFinalResult: async (tournamentId: number): Promise<Blob> => {
    const response = await httpClient.get('/reports/export/final-result', {
      params: {
        tournament_id: tournamentId,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // グループ順位表PDFダウンロード
  downloadGroupStandings: async (params: { tournamentId: number; groupId?: string }): Promise<Blob> => {
    const response = await httpClient.get('/reports/export/group-standings', {
      params: {
        tournament_id: params.tournamentId,
        group_id: params.groupId,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // ===== Excel出力（特別レポート） =====

  // グループ順位表Excelダウンロード
  downloadGroupStandingsExcel: async (params: { tournamentId: number; groupId?: string }): Promise<Blob> => {
    const response = await httpClient.get('/reports/export/group-standings/excel', {
      params: {
        tournament_id: params.tournamentId,
        group_id: params.groupId,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // 最終日組み合わせ表Excelダウンロード
  downloadFinalDayScheduleExcel: async (params: { tournamentId: number; date: string }): Promise<Blob> => {
    const response = await httpClient.get('/reports/export/final-day-schedule/excel', {
      params: {
        tournament_id: params.tournamentId,
        target_date: params.date,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // 最終結果報告書Excelダウンロード
  downloadFinalResultExcel: async (tournamentId: number): Promise<Blob> => {
    const response = await httpClient.get('/reports/export/final-result/excel', {
      params: {
        tournament_id: tournamentId,
      },
      responseType: 'blob',
    });
    return response.data;
  },
};
