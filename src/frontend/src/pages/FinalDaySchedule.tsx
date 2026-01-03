// src/pages/FinalDaySchedule.tsx
// 最終日組み合わせ画面

import { useState, useMemo } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  closestCenter,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { RefreshCw, Save, Calendar, Download, Printer } from 'lucide-react';
import toast from 'react-hot-toast';

import {
  VenueCard,
  KnockoutCard,
  MatchEditModal,
  TeamSlotPreview,
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
  TeamSlot,
  DragItem,
  DropTarget,
  VenueSchedule,
} from '@/features/final-day/types';
import { useTeams } from '@/features/teams/hooks';
import { useAppStore } from '@/stores/appStore';
import { exportScheduleToCSV, printSchedule } from '@/features/final-day/utils/exportSchedule';

export default function FinalDaySchedule() {
  const { currentTournament } = useAppStore();
  const tournamentId = currentTournament?.id || 1;

  // 最終日の日付（大会終了日）
  const finalDayDate = currentTournament?.endDate || new Date().toISOString().split('T')[0];

  // データ取得
  const { data: allMatches, isLoading, refetch } = useFinalDayMatches(tournamentId, finalDayDate);
  const { data: teams = [] } = useTeams(tournamentId);

  // ミューテーション
  const generateFinals = useGenerateFinals(tournamentId);
  const generateTraining = useGenerateTrainingMatches(tournamentId);
  const updateMatchTeams = useUpdateMatchTeams(tournamentId);
  const swapTeams = useSwapTeams(tournamentId);
  const updateFinalsBracket = useUpdateFinalsBracket(tournamentId);

  // ローカルステート
  const [activeItem, setActiveItem] = useState<DragItem | null>(null);
  const [editingMatch, setEditingMatch] = useState<FinalMatch | null>(null);

  // 対戦済み警告用ステート
  const [pendingSwap, setPendingSwap] = useState<{
    from: DragItem;
    to: DropTarget;
    playedInfo: {
      team1Name: string;
      team2Name: string;
      matchDate?: string | null;
      score?: string | null;
    };
  } | null>(null);
  const checkPlayed = useCheckPlayed(tournamentId);

  // センサー設定（マウス＆タッチ対応）
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: 200,
        tolerance: 5,
      },
    })
  );

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
          trainingMap.set(venueId, {
            id: venueId,
            name: match.venue.name,
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
  }, [allMatches]);

  // ドラッグ開始
  const handleDragStart = (event: DragStartEvent) => {
    const data = event.active.data.current as DragItem;
    setActiveItem(data);
  };

  // ドラッグ終了（ドロップ時）
  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveItem(null);

    if (!over) return;

    const dragItem = active.data.current as DragItem;
    const dropTarget = over.data.current as DropTarget;

    // 同じ場所にドロップした場合は何もしない
    if (
      dragItem.matchId === dropTarget.matchId &&
      dragItem.side === dropTarget.side
    ) {
      return;
    }

    // 入れ替え後に同じ試合になるチームIDを取得
    const team1Id = dragItem.team.teamId;
    const team2Id = dropTarget.team?.teamId;

    // 両方のチームIDがある場合、対戦済みかチェック
    if (team1Id && team2Id) {
      try {
        const result = await checkPlayed.mutateAsync({ team1Id, team2Id });
        if (result.played) {
          // 対戦済みの場合、警告ダイアログを表示
          const score = result.homeScore !== null && result.awayScore !== null
            ? `${result.homeScore}-${result.awayScore}`
            : null;
          setPendingSwap({
            from: dragItem,
            to: dropTarget,
            playedInfo: {
              team1Name: dragItem.team.displayName,
              team2Name: dropTarget.team?.displayName || '不明',
              matchDate: result.matchDate,
              score,
            },
          });
          return;
        }
      } catch (error) {
        console.error('Failed to check played:', error);
        // チェック失敗時は続行
      }
    }

    // チーム入れ替え実行
    handleSwapTeams(dragItem, dropTarget);
  };

  // 警告ダイアログで強制確定
  const handleForceSwap = () => {
    if (pendingSwap) {
      handleSwapTeams(pendingSwap.from, pendingSwap.to);
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

  // CSVエクスポート
  const handleExportCSV = () => {
    exportScheduleToCSV(trainingVenues, knockoutMatches, knockoutVenueName, finalDayDate);
    toast.success('CSVをダウンロードしました');
  };

  // 印刷
  const handlePrint = () => {
    printSchedule(trainingVenues, knockoutMatches, knockoutVenueName, finalDayDate);
  };

  // チーム入れ替え
  const handleSwapTeams = async (from: DragItem, to: DropTarget) => {
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
        チームをドラッグして別のチーム枠にドロップすると、チームを入れ替えられます。
        試合行をクリックすると詳細を編集できます。
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
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
                  onMatchClick={setEditingMatch}
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
          />
        </section>

        {/* ドラッグ中のオーバーレイ */}
        <DragOverlay>
          {activeItem && <TeamSlotPreview team={activeItem.team} />}
        </DragOverlay>
      </DndContext>

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
