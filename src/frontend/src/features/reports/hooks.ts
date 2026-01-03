// src/features/reports/hooks.ts
// 報告書 React Query hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportApi } from './api';
import type { ReportGenerateInput, ReportRecipient } from './types';

const QUERY_KEY = ['reports'];

export function useGenerateReport() {
  return useMutation({
    mutationFn: (data: ReportGenerateInput) => reportApi.generate(data),
  });
}

export function useReportJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: [...QUERY_KEY, 'jobs', jobId],
    queryFn: () => reportApi.getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      // 完了またはエラーまでポーリング
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000; // 2秒間隔
    },
  });
}

export function useDownloadReport() {
  return useMutation({
    mutationFn: async (jobId: string) => {
      const blob = await reportApi.download(jobId);
      // ブラウザでダウンロード
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${jobId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    },
  });
}

export function useReportRecipients(tournamentId: number) {
  return useQuery({
    queryKey: [...QUERY_KEY, 'recipients', tournamentId],
    queryFn: () => reportApi.getRecipients(tournamentId),
    enabled: tournamentId > 0,
  });
}

export function useAddReportRecipient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<ReportRecipient, 'id'>) => reportApi.addRecipient(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [...QUERY_KEY, 'recipients', variables.tournamentId],
      });
    },
  });
}

export function useUpdateReportRecipient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ReportRecipient> }) =>
      reportApi.updateRecipient(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, 'recipients'] });
    },
  });
}

export function useDeleteReportRecipient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => reportApi.deleteRecipient(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, 'recipients'] });
    },
  });
}
