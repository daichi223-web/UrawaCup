// src/pages/FinalDaySchedule.tsx
// 最終日組み合わせ画面（クリック入れ替え方式）

import { useState, useMemo, useRef } from 'react';
import { RefreshCw, Save, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';

import {
  VenueCard,
  KnockoutCard,
  MatchEditModal,
  PlayedWarningDialog,
} from '@/features/final-day/components';
import {
  useFinalDayMatches,
  useGenerateFinals,
  useGenerateTrainingMatches,
  useUpdateMatchTeams,
  useSwapTeams,
  useCheckPlayed,
  useUpdateFinalsBracket,
} from '@/features/final-day/hooks';
import type {
  FinalMatch,
  VenueSchedule,
} from '@/features/final-day/types';
import { useTeams } from '@/features/teams/hooks';
import { useVenuesByTournament, useUpdateVenue } from '@/features/venues/hooks';
import { useAppStore } from '@/stores/appStore';

// クリック入れ替え用の型
interface SwapSlot {
  matchId: number;
  side: 'home' | 'away';
  teamId?: number;
  displayName: string;
}

export default function FinalDaySchedule() {
  const { currentTournament } = useAppStore();
  const tournamentId = currentTournament?.id || 1;

  // 最終日の日付（大会終了日）
  const finalDayDate = currentTournament?.endDate || new Date().toISOString().split('T')[0];

  // データ取得
  const { data: allMatches, isLoading, refetch } = useFinalDayMatches(tournamentId, finalDayDate);
  const { data: teams = [] } = useTeams(tournamentId);
  const { data: venues = [] } = useVenuesByTournament(tournamentId);

  // ミューテーション
  const generateFinals = useGenerateFinals(tournamentId);
  const generateTraining = useGenerateTrainingMatches(tournamentId);
  const updateMatchTeams = useUpdateMatchTeams(tournamentId);
  const swapTeams = useSwapTeams(tournamentId);
  const updateFinalsBracket = useUpdateFinalsBracket(tournamentId);
  const updateVenue = useUpdateVenue();

  // ローカルステート
  const [editingMatch, setEditingMatch] = useState<FinalMatch | null>(null);

  // クリック入れ替えモード用ステート
  const [selectedSlot, setSelectedSlot] = useState<SwapSlot | null>(null);

  // 対戦済み警告用ステート
  const [pendingSwap, setPendingSwap] = useState<{
    from: SwapSlot;
    to: SwapSlot;
    playedInfo: {
      team1Name: string;
      team2Name: string;
      matchDate?: string | null;
      score?: string | null;
    };
  } | null>(null);
  const checkPlayed = useCheckPlayed(tournamentId);

  // 連打防止用ref
  const swappingRef = useRef<Set<number>>(new Set());

  // 試合を会場別・種別別に分類
  const { trainingVenues, knockoutMatches, knockoutVenueName } = useMemo(() => {
    if (!allMatches) {
      return { trainingVenues: [], knockoutMatches: [], knockoutVenueName: '' };
    }

    // 研修試合（会場別）
    const trainingMap = new Map<number, VenueSchedule>();
    // 決勝トーナメント
    const knockout: FinalMatch[] = [];
    let koVenue = '駒場スタジアム';

    allMatches.forEach((match) => {
      if (match.matchType === 'training') {
        const venueId = match.venue.id;
        if (!trainingMap.has(venueId)) {
          // venues dataから会場担当情報を取得
          const venueData = venues.find(v => v.id === venueId);
          // managerTeamId または snake_case の manager_team_id を使用
          const managerId = venueData?.managerTeamId ?? venueData?.manager_team_id;
          const managerTeam = managerId
            ? teams.find(t => t.id === managerId)
            : null;

          trainingMap.set(venueId, {
            id: venueId,
            name: match.venue.name,
            manager: managerTeam?.shortName || managerTeam?.name,
            matches: [],
          });
        }
        trainingMap.get(venueId)!.matches.push(match);
      } else {
        knockout.push(match);
        if (match.venue.name) {
          koVenue = match.venue.name;
        }
      }
    });

    // 各会場の試合を時間順にソート
    trainingMap.forEach((venue) => {
      venue.matches.sort((a, b) => a.matchOrder - b.matchOrder);
    });

    return {
      trainingVenues: Array.from(trainingMap.values()),
      knockoutMatches: knockout,
      knockoutVenueName: koVenue,
    };
  }, [allMatches, venues, teams]);

  // チーム入れ替え実行
  const executeSwap = async (from: SwapSlot, to: SwapSlot) => {
    // 同じ試合に対する重複呼び出しを防止
    if (swappingRef.current.has(from.matchId)) {
      console.log('[SwapTeams] 重複呼び出しをスキップ:', from.matchId);
      return;
    }
    swappingRef.current.add(from.matchId);

    try {
      await swapTeams.mutateAsync({
        match1Id: from.matchId,
        side1: from.side,
        match2Id: to.matchId,
        side2: to.side,
      });
      toast.success('チームを入れ替えました');
    } catch (error) {
      console.error('Failed to swap teams:', error);
      toast.error('チームの入れ替えに失敗しました');
    } finally {
      // 少し遅延してから解除（連打防止）
      setTimeout(() => {
        swappingRef.current.delete(from.matchId);
      }, 500);
    }
  };

  // クリック入れ替えモード: チームスロットクリック時
  const handleSlotClick = async (matchId: number, side: 'home' | 'away') => {
    // クリックされたスロットの情報を取得
    const match = allMatches?.find(m => m.id === matchId);
    if (!match) return;

    const clickedTeam = side === 'home' ? match.homeTeam : match.awayTeam;
    const clickedSlot: SwapSlot = {
      matchId,
      side,
      teamId: clickedTeam.teamId,
      displayName: clickedTeam.displayName,
    };

    // 選択解除
    if (selectedSlot?.matchId === matchId && selectedSlot?.side === side) {
      setSelectedSlot(null);
      return;
    }

    // 既に選択中のスロットがある場合は入れ替え実行
    if (selectedSlot) {
      const team1Id = selectedSlot.teamId;
      const team2Id = clickedSlot.teamId;

      // 対戦済みチェック
      if (team1Id && team2Id) {
        try {
          const result = await checkPlayed.mutateAsync({ team1Id, team2Id });
          if (result.played) {
            const score = result.homeScore !== null && result.awayScore !== null
              ? `${result.homeScore}-${result.awayScore}`
              : null;
            setPendingSwap({
              from: selectedSlot,
              to: clickedSlot,
              playedInfo: {
                team1Name: selectedSlot.displayName,
                team2Name: clickedSlot.displayName,
                matchDate: result.matchDate,
                score,
              },
            });
            setSelectedSlot(null);
            return;
          }
        } catch (error) {
          console.error('Failed to check played:', error);
        }
      }

      // 入れ替え実行
      executeSwap(selectedSlot, clickedSlot);
      setSelectedSlot(null);
      return;
    }

    // 最初のクリック: 選択状態にする
    setSelectedSlot(clickedSlot);
  };

  // 警告ダイアログで強制確定
  const handleForceSwap = () => {
    if (pendingSwap) {
      executeSwap(pendingSwap.from, pendingSwap.to);
      setPendingSwap(null);
    }
  };

  // 警告ダイアログをキャンセル
  const handleCancelSwap = () => {
    setPendingSwap(null);
  };

  // 準決勝結果を3決・決勝に反映
  const handleUpdateBracket = async () => {
    try {
      await updateFinalsBracket.mutateAsync();
      toast.success('準決勝結果を反映しました');
      refetch();
    } catch (error) {
      console.error('Failed to update bracket:', error);
      toast.error('結果反映に失敗しました');
    }
  };

  // 自動生成
  const handleGenerate = async () => {
    if (!confirm('最終日の組み合わせを自動生成しますか？\n既存の試合は上書きされます。')) {
      return;
    }

    try {
      await generateFinals.mutateAsync({
        matchDate: finalDayDate,
        startTime: '09:00',
      });
      await generateTraining.mutateAsync({
        matchDate: finalDayDate,
        startTime: '09:30',
      });
      toast.success('組み合わせを生成しました');
      refetch();
    } catch (error) {
      console.error('Failed to generate schedule:', error);
      toast.error('生成に失敗しました');
    }
  };

  // 試合編集保存
  const handleSaveMatch = async (match: FinalMatch) => {
    if (!match.homeTeam.teamId || !match.awayTeam.teamId) return;

    try {
      await updateMatchTeams.mutateAsync({
        matchId: match.id,
        homeTeamId: match.homeTeam.teamId,
        awayTeamId: match.awayTeam.teamId,
      });
      toast.success('保存しました');
      setEditingMatch(null);
      refetch();
    } catch (error) {
      console.error('Failed to save match:', error);
      toast.error('保存に失敗しました');
    }
  };

  // 会場担当変更
  const handleManagerChange = async (venueId: number, teamId: number | null) => {
    try {
      await updateVenue.mutateAsync({
        id: venueId,
        managerTeamId: teamId,
      });
      toast.success('会場担当を変更しました');
    } catch (error) {
      console.error('Failed to update venue manager:', error);
      toast.error('会場担当の変更に失敗しました');
    }
  };

  // 日付フォーマット
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const days = ['日', '月', '火', '水', '木', '金', '土'];
    return `${date.getMonth() + 1}月${date.getDate()}日（${days[date.getDay()]}）`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-7xl mx-auto">
      {/* ヘッダー */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Calendar size={24} />
            最終日 組み合わせ
          </h1>
          <p className="text-gray-600 text-sm mt-1">
            {formatDate(finalDayDate)}【順位リーグ・決勝トーナメント】
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleGenerate}
            disabled={generateFinals.isPending || generateTraining.isPending}
            className="flex items-center gap-2 px-4 py-2 border rounded hover:bg-gray-100 disabled:opacity-50"
          >
            <RefreshCw size={16} className={generateFinals.isPending ? 'animate-spin' : ''} />
            自動生成
          </button>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Save size={16} />
            更新
          </button>
        </div>
      </div>

      {/* ヒント */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6 text-sm text-blue-800">
        {selectedSlot ? (
          <span className="font-medium text-blue-900">
            「{selectedSlot.displayName}」を選択中 - 入れ替え先のチームをクリックしてください（キャンセル: 同じチームを再クリック）
          </span>
        ) : (
          <>
            チームをクリックして選択後、別のチームをクリックで入れ替えできます。
            試合行をクリックすると詳細を編集できます。
          </>
        )}
      </div>

      {/* 順位リーグ（研修試合） */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3 pb-2 border-b">
          【順位リーグ】
        </h2>
        {trainingVenues.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {trainingVenues.map((venue) => (
              <VenueCard
                key={venue.id}
                venue={venue}
                teams={teams}
                onMatchClick={setEditingMatch}
                onManagerChange={handleManagerChange}
                selectedSlot={selectedSlot}
                onSlotClick={handleSlotClick}
              />
            ))}
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
            研修試合がありません。「自動生成」ボタンで生成してください。
          </div>
        )}
      </section>

      {/* 決勝トーナメント */}
      <section>
        <h2 className="text-lg font-semibold mb-3 pb-2 border-b">
          【3決・決勝戦】
        </h2>
        <KnockoutCard
          venueName={knockoutVenueName}
          matches={knockoutMatches}
          onMatchClick={setEditingMatch}
          onUpdateBracket={handleUpdateBracket}
          isUpdating={updateFinalsBracket.isPending}
          selectedSlot={selectedSlot}
          onSlotClick={handleSlotClick}
        />
      </section>

      {/* 編集モーダル */}
      {editingMatch && (
        <MatchEditModal
          match={editingMatch}
          teams={teams}
          onSave={handleSaveMatch}
          onClose={() => setEditingMatch(null)}
        />
      )}

      {/* 対戦済み警告ダイアログ */}
      <PlayedWarningDialog
        isOpen={!!pendingSwap}
        team1Name={pendingSwap?.playedInfo.team1Name || ''}
        team2Name={pendingSwap?.playedInfo.team2Name || ''}
        matchDate={pendingSwap?.playedInfo.matchDate}
        score={pendingSwap?.playedInfo.score}
        onConfirm={handleForceSwap}
        onCancel={handleCancelSwap}
      />
    </div>
  );
}
