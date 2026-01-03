// src/features/final-day/hooks.ts
// 最終日組み合わせ用フック

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { finalDayApi } from './api';
import type { SwapTeamsRequest } from './types';
import { toFinalMatch } from './types';

// Query Keys
export const finalDayKeys = {
  all: ['final-day'] as const,
  finals: (tournamentId: number) => [...finalDayKeys.all, 'finals', tournamentId] as const,
  training: (tournamentId: number) => [...finalDayKeys.all, 'training', tournamentId] as const,
  day: (tournamentId: number, date: string) => [...finalDayKeys.all, 'day', tournamentId, date] as const,
};

/**
 * 決勝トーナメント試合を取得
 */
export function useFinalMatches(tournamentId: number) {
  return useQuery({
    queryKey: finalDayKeys.finals(tournamentId),
    queryFn: () => finalDayApi.getFinalMatches(tournamentId),
    select: (data) => data.map(toFinalMatch),
    enabled: !!tournamentId,
  });
}

/**
 * 研修試合を取得
 */
export function useTrainingMatches(tournamentId: number, matchDate?: string) {
  return useQuery({
    queryKey: finalDayKeys.training(tournamentId),
    queryFn: () => finalDayApi.getTrainingMatches(tournamentId, matchDate),
    select: (data) => data.map(toFinalMatch),
    enabled: !!tournamentId,
  });
}

/**
 * 最終日の全試合を取得
 */
export function useFinalDayMatches(tournamentId: number, matchDate: string) {
  return useQuery({
    queryKey: finalDayKeys.day(tournamentId, matchDate),
    queryFn: () => finalDayApi.getFinalDayMatches(tournamentId, matchDate),
    select: (data) => data.map(toFinalMatch),
    enabled: !!tournamentId && !!matchDate,
  });
}

/**
 * 決勝トーナメント自動生成
 */
export function useGenerateFinals(tournamentId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { matchDate: string; startTime?: string; venueId?: number }) =>
      finalDayApi.generateFinals(tournamentId, params.matchDate, params.startTime, params.venueId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: finalDayKeys.finals(tournamentId) });
      queryClient.invalidateQueries({ queryKey: finalDayKeys.all });
    },
  });
}

/**
 * 研修試合自動生成
 */
export function useGenerateTrainingMatches(tournamentId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { matchDate: string; startTime?: string; minVenues?: number }) =>
      finalDayApi.generateTrainingMatches(tournamentId, params.matchDate, params.startTime, params.minVenues),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: finalDayKeys.training(tournamentId) });
      queryClient.invalidateQueries({ queryKey: finalDayKeys.all });
    },
  });
}

/**
 * 準決勝結果に基づく組み合わせ更新
 */
export function useUpdateFinalsBracket(tournamentId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => finalDayApi.updateFinalsBracket(tournamentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: finalDayKeys.finals(tournamentId) });
    },
  });
}

/**
 * 試合のチーム変更
 */
export function useUpdateMatchTeams(_tournamentId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { matchId: number; homeTeamId: number; awayTeamId: number }) =>
      finalDayApi.updateMatchTeams(params.matchId, params.homeTeamId, params.awayTeamId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: finalDayKeys.all });
    },
  });
}

/**
 * チーム入れ替え
 */
export function useSwapTeams(_tournamentId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SwapTeamsRequest) => finalDayApi.swapTeams(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: finalDayKeys.all });
    },
  });
}

/**
 * 試合削除
 */
export function useDeleteFinalMatch(_tournamentId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (matchId: number) => finalDayApi.deleteMatch(matchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: finalDayKeys.all });
    },
  });
}

/**
 * 対戦済みチェック
 */
export function useCheckPlayed(tournamentId: number) {
  return useMutation({
    mutationFn: (params: { team1Id: number; team2Id: number }) =>
      finalDayApi.checkPlayed(tournamentId, params.team1Id, params.team2Id),
  });
}
