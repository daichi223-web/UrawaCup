import { Calendar, Users, Trophy, FileText, Clock } from 'lucide-react'
import { useState, useEffect } from 'react';
import { matchApi } from '@/features/matches';
import api from '@/core/http';
import { Team } from '@shared/types';
import { useAppStore } from '@/stores/appStore';
import LoadingSpinner from '../components/common/LoadingSpinner';

/**
 * ダッシュボード画面
 * 大会進行状況とクイックアクセスを提供
 */
function Dashboard() {
  const [loading, setLoading] = useState(true);
  const { currentTournament: tournament } = useAppStore();
  const [stats, setStats] = useState({
    totalTeams: 24,
    registeredTeams: 0,
    totalMatches: 48 + 4, // 予選48 + 決勝T4 (目安)
    completedMatches: 0,
    pendingReports: 0,
  });

  // TODO: Contextから取得
  const tournamentId = 1;

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // 大会情報はLayoutで取得済みのためスキップ

        // チーム数
        const teamsResponse = await api.get<{ teams: Team[]; total: number }>(`/teams/?tournament_id=${tournamentId}`);

        // 試合数
        const matchesResponse = await matchApi.getMatches({ tournament_id: tournamentId, limit: 1000 });
        const matches = matchesResponse.matches;

        setStats({
          totalTeams: 24,
          registeredTeams: teamsResponse.data.teams.length,
          totalMatches: matches.length,
          completedMatches: matches.filter(m => m.status === 'completed').length,
          pendingReports: 0, // TODO: Implement report logic
        });

      } catch (err) {
        console.error('Failed to fetch dashboard data', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [tournamentId]);

  if (loading) return <LoadingSpinner />;
  if (!tournament) return <div>大会データが見つかりません</div>;

  return (
    <div className="space-y-6">
      {/* ページヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
        <p className="text-gray-600 mt-1">大会運営の概要を確認できます</p>
      </div>

      {/* 大会情報カード */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {tournament.name}
              </h2>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {tournament.startDate} 〜 {tournament.endDate}
                </span>
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full">
                  第{tournament.edition}回
                </span>
              </div>
            </div>
            {/* Status logic can be improved based on date */}
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              開催中
            </span>
          </div>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="登録チーム"
          value={`${stats.registeredTeams} / ${stats.totalTeams}`}
          color="blue"
        />
        <StatCard
          icon={Trophy}
          label="完了試合"
          value={`${stats.completedMatches} / ${stats.totalMatches}`}
          color="green"
        />
        <StatCard
          icon={FileText}
          label="未送信報告書"
          value={stats.pendingReports.toString()}
          color="yellow"
        />
        <StatCard
          icon={Clock}
          label="次の試合"
          value={stats.totalMatches > stats.completedMatches ? "進行中" : "完了"}
          color="gray"
        />
      </div>

      {/* クイックアクション */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">クイックアクション</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <QuickActionButton
              href="/teams"
              label="チーム登録"
              description="参加チームの登録・編集"
              icon={Users}
            />
            <QuickActionButton
              href="/results"
              label="試合結果入力"
              description="スコア・得点者を入力"
              icon={Trophy}
            />
            <QuickActionButton
              href="/standings"
              label="順位表確認"
              description="グループ別順位・星取表"
              icon={Trophy}
            />
            <QuickActionButton
              href="/schedule"
              label="日程管理"
              description="試合日程の生成・確認"
              icon={Calendar}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

// 統計カードコンポーネント
interface StatCardProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  color: 'blue' | 'green' | 'yellow' | 'gray'
}

function StatCard({ icon: Icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    gray: 'bg-gray-100 text-gray-600',
  }

  return (
    <div className="card">
      <div className="card-body flex items-center gap-4">
        <div
          className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[color]}`}
        >
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm text-gray-600">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

// クイックアクションボタンコンポーネント
interface QuickActionButtonProps {
  href: string
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
}

function QuickActionButton({
  href,
  label,
  description,
  icon: Icon,
}: QuickActionButtonProps) {
  return (
    <a
      href={href}
      className="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors"
    >
      <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
        <Icon className="w-5 h-5 text-primary-600" />
      </div>
      <div>
        <p className="font-medium text-gray-900">{label}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
    </a>
  )
}

export default Dashboard
