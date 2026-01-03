import { Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy, useEffect, useState } from 'react'
import Layout from './components/Layout'
import LoadingSpinner from './components/common/LoadingSpinner'
import { RequireAdmin, RequireVenueManager } from './components/auth'
import { useAuthStore } from './stores/authStore'

// PWAコンポーネント
import { UpdatePrompt, InstallPrompt, ConflictResolver } from './components/pwa'
import { useSyncState } from './hooks/usePWA'

// ページコンポーネントを遅延読み込み
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const TeamManagement = lazy(() => import('./pages/TeamManagement'))
const MatchSchedule = lazy(() => import('./pages/MatchSchedule'))
const MatchResult = lazy(() => import('./pages/MatchResult'))
const Standings = lazy(() => import('./pages/Standings'))
const Reports = lazy(() => import('./pages/Reports'))
const Settings = lazy(() => import('./pages/Settings'))
const PublicLayout = lazy(() => import('./components/PublicLayout'))
const PublicMatchList = lazy(() => import('./pages/public/PublicMatchList'))
const PublicStandings = lazy(() => import('./pages/public/PublicStandings'))
const MatchApproval = lazy(() => import('./pages/MatchApproval'))
const ExclusionSettings = lazy(() => import('./pages/ExclusionSettings'))
const ScorerRanking = lazy(() => import('./pages/ScorerRanking'))
const PlayerManagement = lazy(() => import('./pages/PlayerManagement'))
const FinalDaySchedule = lazy(() => import('./pages/FinalDaySchedule'))

/**
 * メインアプリケーションコンポーネント
 * 浦和カップ トーナメント管理システム
 */
function App() {
  const { checkAuth } = useAuthStore()
  const { conflictCount } = useSyncState()
  const [showConflictResolver, setShowConflictResolver] = useState(false)

  // アプリ起動時に認証状態を確認
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // 競合がある場合は自動的にダイアログを表示
  useEffect(() => {
    if (conflictCount > 0) {
      setShowConflictResolver(true)
    }
  }, [conflictCount])

  return (
    <>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          {/* ログインページ（レイアウトなし） */}
          <Route path="/login" element={<Login />} />

          {/* メインレイアウト内のルート */}
          <Route element={<Layout />}>
            {/* ダッシュボード（閲覧可能） */}
            <Route path="/" element={<Dashboard />} />

            {/* 順位表（閲覧可能） */}
            <Route path="/standings" element={<Standings />} />

            {/* 得点ランキング（閲覧可能） */}
            <Route path="/scorer-ranking" element={<ScorerRanking />} />

            {/* チーム管理（管理者専用） */}
            <Route
              path="/teams"
              element={
                <RequireAdmin>
                  <TeamManagement />
                </RequireAdmin>
              }
            />

            {/* 日程管理（管理者専用） */}
            <Route
              path="/schedule"
              element={
                <RequireAdmin>
                  <MatchSchedule />
                </RequireAdmin>
              }
            />

            {/* 試合結果入力（会場担当者以上） */}
            <Route
              path="/results"
              element={
                <RequireVenueManager>
                  <MatchResult />
                </RequireVenueManager>
              }
            />

            {/* 報告書出力（管理者専用） */}
            <Route
              path="/reports"
              element={
                <RequireAdmin>
                  <Reports />
                </RequireAdmin>
              }
            />

            {/* 結果承認（管理者専用） */}
            <Route
              path="/approval"
              element={
                <RequireAdmin>
                  <MatchApproval />
                </RequireAdmin>
              }
            />

            {/* 設定（管理者専用） */}
            <Route
              path="/settings"
              element={
                <RequireAdmin>
                  <Settings />
                </RequireAdmin>
              }
            />

            {/* 対戦除外設定（管理者専用） */}
            <Route
              path="/exclusions"
              element={
                <RequireAdmin>
                  <ExclusionSettings />
                </RequireAdmin>
              }
            />

            {/* 選手管理（管理者専用） */}
            <Route
              path="/players"
              element={
                <RequireAdmin>
                  <PlayerManagement />
                </RequireAdmin>
              }
            />

            {/* 最終日組み合わせ（管理者専用） */}
            <Route
              path="/final-day"
              element={
                <RequireAdmin>
                  <FinalDaySchedule />
                </RequireAdmin>
              }
            />
          </Route>

          {/* Public Routes (No Auth Required) */}
          <Route path="/public" element={<PublicLayout />}>
            <Route index element={<Navigate to="matches" replace />} />
            <Route path="matches" element={<PublicMatchList />} />
            <Route path="standings" element={<PublicStandings />} />
          </Route>

          {/* 404リダイレクト */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>

      {/* PWAコンポーネント */}
      <UpdatePrompt />
      <InstallPrompt />

      {/* 競合解決ダイアログ */}
      {showConflictResolver && (
        <ConflictResolver
          onResolve={() => setShowConflictResolver(false)}
        />
      )}
    </>
  )
}

export default App
