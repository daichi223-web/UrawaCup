/**
 * 順位表画面
 * グループ別順位表示（リアルタイム更新対応）
 *
 * リアルタイム更新対応:
 * - WebSocket経由で順位表の更新通知を受信
 * - React Queryと連携して自動的にデータを再取得
 * - 5秒間隔でポーリング（バックアップ）
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, AlertCircle, WifiOff, Clock, Printer } from 'lucide-react';
import { standingApi, type GroupStandings } from '@/features/standings';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';
import LoadingSpinner from '../components/common/LoadingSpinner';
// 印刷用スタイル（2x2レイアウトで1ページに収める）
const printStyles = `
@media print {
  @page { size: A4 landscape; margin: 8mm; }
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    font-size: 9px !important;
  }
  .no-print { display: none !important; }
  nav, header, aside, footer, .sidebar { display: none !important; }

  /* 2x2グリッドレイアウト */
  .standings-grid {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
  }

  /* カードをコンパクトに */
  .standings-grid .card {
    break-inside: avoid;
    page-break-inside: avoid;
    margin: 0 !important;
    box-shadow: none !important;
    border: 1px solid #ddd !important;
  }

  .standings-grid .card-header {
    padding: 4px 8px !important;
    font-size: 11px !important;
  }

  /* テーブルをコンパクトに */
  .standings-grid table {
    font-size: 8px !important;
  }

  .standings-grid th,
  .standings-grid td {
    padding: 2px 4px !important;
    line-height: 1.2 !important;
  }

  .standings-grid th {
    font-size: 7px !important;
  }

  /* タイトル調整 */
  .print-content h1 {
    font-size: 16px !important;
    margin-bottom: 8px !important;
  }

  .print-content .space-y-6 > * {
    margin-top: 8px !important;
  }
}
`;


function Standings() {
  // TODO: Get active tournament ID from context or store
  const tournamentId = 1;

  // アニメーション用の更新フラグ
  const [recentlyUpdated, setRecentlyUpdated] = useState(false);

  // リアルタイム更新フック
  const { connectionState } = useRealtimeUpdates({
    tournamentId,
    showNotifications: true,
  });

  const isConnected = connectionState === 'connected';

  // React Query を使用してデータを取得（リアルタイム更新と連携）
  const {
    data: groupStandings = [],
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useQuery<GroupStandings[]>({
    queryKey: ['standings', tournamentId],
    queryFn: () => standingApi.getStandingsByGroup(tournamentId),
    // 自動リフェッチの設定
    refetchOnWindowFocus: true,
    staleTime: 5000, // 5秒間はフレッシュとみなす
    refetchInterval: 10000, // 10秒ごとにポーリング（WebSocketのバックアップ）
  });

  // データ更新時のアニメーション
  useEffect(() => {
    if (dataUpdatedAt) {
      setRecentlyUpdated(true);
      const timer = setTimeout(() => setRecentlyUpdated(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [dataUpdatedAt]);

  // 最終更新時刻のフォーマット
  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString('ja-JP')
    : null;

  // 印刷ハンドラー
  const handlePrint = () => window.print();

  if (isLoading) return <LoadingSpinner />;
  if (isError) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-500">順位表の取得に失敗しました</p>
        <p className="text-gray-500 text-sm mt-2">{(error as Error)?.message}</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          再試行
        </button>
      </div>
    );
  }

  return (
    <>
      {/* 印刷用スタイル */}
      <style>{printStyles}</style>
      <div className="space-y-6 print-content">
      {/* ページヘッダー */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">順位表</h1>
            <p className="text-gray-600 mt-1">
              各グループの順位を確認できます
            </p>
          </div>
          {/* LIVE インジケーター */}
          <div className={`no-print flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${
            isConnected
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-500'
          }`}>
            {isConnected ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                LIVE
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                オフライン
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4 no-print">
          {/* 最終更新時刻 */}
          {lastUpdated && (
            <span className={`text-sm flex items-center gap-1.5 transition-colors ${
              recentlyUpdated ? 'text-green-600 font-medium' : 'text-gray-500'
            }`}>
              <Clock className="w-4 h-4" />
              最終更新: {lastUpdated}
              {isFetching && !isLoading && (
                <span className="ml-2 text-primary-600">更新中...</span>
              )}
            </span>
          )}
          {/* PDF印刷ボタン */}
            <button
              onClick={handlePrint}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              <Printer className="w-4 h-4" />
              PDF印刷
            </button>
            {/* 手動更新ボタン */}
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            更新
          </button>
        </div>
      </div>

      {/* 暫定順位の注意書き */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2 no-print">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-amber-800">
          <p className="font-medium">暫定順位表</p>
          <p className="text-amber-700">
            試合結果が入力されるとリアルタイムで更新されます。
            全試合終了まで順位は確定しません。
          </p>
        </div>
      </div>

      {/* グループ別順位表 */}
      <div className={`standings-grid grid grid-cols-1 xl:grid-cols-2 gap-6 transition-opacity duration-300 ${
        recentlyUpdated ? 'opacity-80' : 'opacity-100'
      }`}>
        {groupStandings.map((groupData) => (
          <div key={groupData.groupId} className={`card transition-shadow ${
            recentlyUpdated ? 'shadow-lg ring-2 ring-green-200' : ''
          }`}>
            <div className={`card-header group-${groupData.groupId.toLowerCase()} flex justify-between items-center`}>
              <h3 className="text-lg font-semibold">{groupData.groupId}グループ</h3>
              {groupData.needsTiebreaker && (
                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                  同順位あり
                </span>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="table w-full">
                <thead>
                  <tr className="text-xs uppercase bg-gray-50 border-b">
                    <th className="px-4 py-3 text-left font-medium text-gray-500 w-12">順位</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">チーム</th>
                    <th className="px-2 py-3 text-center font-medium text-gray-500 w-10">試</th>
                    <th className="px-2 py-3 text-center font-medium text-gray-500 w-10">勝</th>
                    <th className="px-2 py-3 text-center font-medium text-gray-500 w-10">分</th>
                    <th className="px-2 py-3 text-center font-medium text-gray-500 w-10">敗</th>
                    <th className="px-2 py-3 text-center font-medium text-gray-500 w-10">得</th>
                    <th className="px-2 py-3 text-center font-medium text-gray-500 w-10">失</th>
                    <th className="px-2 py-3 text-center font-medium text-gray-500 w-10">差</th>
                    <th className="px-4 py-3 text-center font-bold text-gray-700 w-12 bg-gray-50">点</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {groupData.standings.map((standing, index) => (
                    <tr
                      key={standing.teamId}
                      className={`hover:bg-gray-50 transition-colors ${
                        index < 2 ? 'bg-green-50/50' : '' // 上位2チームをハイライト
                      }`}
                    >
                      <td className="px-4 py-3 font-semibold text-gray-900 border-r">
                        <span className={`${
                          standing.rank === 1 ? 'text-yellow-600' :
                          standing.rank === 2 ? 'text-gray-500' : ''
                        }`}>
                          {standing.rank}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-900 font-medium">
                        {standing.team?.name ?? `Team ${standing.teamId}`}
                        {standing.rankReason && (
                          <span className="ml-2 text-xs text-blue-500" title={standing.rankReason}>ℹ️</span>
                        )}
                      </td>
                      <td className="px-2 py-3 text-center text-gray-600">{standing.played}</td>
                      <td className="px-2 py-3 text-center text-gray-600">{standing.won}</td>
                      <td className="px-2 py-3 text-center text-gray-600">{standing.drawn}</td>
                      <td className="px-2 py-3 text-center text-gray-600">{standing.lost}</td>
                      <td className="px-2 py-3 text-center text-gray-600">{standing.goalsFor}</td>
                      <td className="px-2 py-3 text-center text-gray-600">{standing.goalsAgainst}</td>
                      <td className="px-2 py-3 text-center font-medium text-gray-900">
                        {standing.goalDifference > 0 ? `+${standing.goalDifference}` : standing.goalDifference}
                      </td>
                      <td className="px-4 py-3 text-center font-bold text-blue-600 bg-blue-50">
                        {standing.points}
                      </td>
                    </tr>
                  ))}
                  {groupData.standings.length === 0 && (
                    <tr>
                      <td colSpan={10} className="text-center py-8 text-gray-400">
                        データがありません
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

      {/* 順位決定ルール説明 */}
      <div className="card no-print">
        <div className="card-header">
          <h3 className="text-lg font-semibold">順位決定ルール</h3>
        </div>
        <div className="card-body">
          <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
            <li>勝点（勝利=3点、引分=1点、敗北=0点）</li>
            <li>得失点差（ゴールディファレンス）</li>
            <li>総得点</li>
            <li>当該チーム間の対戦成績</li>
            <li>抽選</li>
          </ol>
          <p className="mt-3 text-xs text-gray-500">
            ※ 各グループ上位2チームが決勝トーナメントに進出します
          </p>
        </div>
      </div>
      </div>
    </>
  )
}

export default Standings
