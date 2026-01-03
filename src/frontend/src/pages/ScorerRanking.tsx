/**
 * 得点ランキング画面
 * 大会全体の得点者ランキングを表示
 */

import { useQuery } from '@tanstack/react-query';
import { RefreshCw, AlertCircle, Trophy, Medal } from 'lucide-react';
import { standingApi, type TopScorer } from '@/features/standings';
import LoadingSpinner from '../components/common/LoadingSpinner';

function ScorerRanking() {
  // TODO: Get active tournament ID from context or store
  const tournamentId = 1;

  const {
    data: scorers = [],
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useQuery<TopScorer[]>({
    queryKey: ['top-scorers', tournamentId],
    queryFn: () => standingApi.getTopScorers(tournamentId, 30),
    refetchOnWindowFocus: true,
    staleTime: 30000,
  });

  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString('ja-JP')
    : null;

  // 順位に応じたメダルアイコンを返す
  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className="w-5 h-5 text-yellow-500" />;
      case 2:
        return <Medal className="w-5 h-5 text-gray-400" />;
      case 3:
        return <Medal className="w-5 h-5 text-amber-600" />;
      default:
        return null;
    }
  };

  // 順位に応じた背景色クラスを返す
  const getRankBgClass = (rank: number) => {
    switch (rank) {
      case 1:
        return 'bg-yellow-50';
      case 2:
        return 'bg-gray-50';
      case 3:
        return 'bg-amber-50';
      default:
        return '';
    }
  };

  if (isLoading) return <LoadingSpinner />;

  if (isError) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-500">得点ランキングの取得に失敗しました</p>
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
    <div className="space-y-6">
      {/* ページヘッダー */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">得点ランキング</h1>
          <p className="text-gray-600 mt-1">
            大会の得点者ランキングを確認できます（研修試合を除く）
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              最終更新: {lastUpdated}
              {isFetching && !isLoading && (
                <span className="ml-2 text-primary-600">更新中...</span>
              )}
            </span>
          )}
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

      {/* 得点ランキング表 */}
      <div className="card">
        <div className="card-header bg-gradient-to-r from-primary-600 to-primary-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Trophy className="w-5 h-5" />
            得点ランキング
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="table w-full">
            <thead>
              <tr className="text-xs uppercase bg-gray-50 border-b">
                <th className="px-4 py-3 text-center font-medium text-gray-500 w-16">順位</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">選手名</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">所属チーム</th>
                <th className="px-4 py-3 text-center font-bold text-gray-700 w-20 bg-blue-50">得点</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {scorers.map((scorer) => (
                <tr
                  key={`${scorer.teamId}-${scorer.scorerName}`}
                  className={`hover:bg-gray-50 transition-colors ${getRankBgClass(scorer.rank)}`}
                >
                  <td className="px-4 py-3 text-center font-semibold text-gray-900">
                    <div className="flex items-center justify-center gap-2">
                      {getRankIcon(scorer.rank)}
                      <span className={scorer.rank <= 3 ? 'text-lg' : ''}>
                        {scorer.rank}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-900 font-medium">
                    {scorer.scorerName}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {scorer.teamName}
                  </td>
                  <td className="px-4 py-3 text-center font-bold text-blue-600 bg-blue-50 text-lg">
                    {scorer.goals}
                  </td>
                </tr>
              ))}
              {scorers.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center py-8 text-gray-400">
                    得点データがありません
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 注釈 */}
      <div className="card">
        <div className="card-body">
          <p className="text-sm text-gray-500">
            * 研修試合での得点は含まれません
          </p>
          <p className="text-sm text-gray-500">
            * オウンゴールは得点としてカウントされません
          </p>
        </div>
      </div>
    </div>
  );
}

export default ScorerRanking;
