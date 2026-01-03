import { ReactNode, useState } from 'react'
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom'
import {
  Home,
  Users,
  Calendar,
  ClipboardEdit,
  Trophy,
  FileText,
  Settings,
  Menu,
  X,
  LogIn,
  LogOut,
  User,
  Shield,
  Wifi,
  type LucideIcon,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuthStore } from '@/stores/authStore'
import type { UserRole } from '@shared/types'
import { OfflineIndicator } from './pwa'
import { ConnectionStatus } from './common/ConnectionStatus'
import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import api from '@/core/http'
import type { Tournament } from '@shared/types'
import { useAppStore } from '@/stores/appStore'
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates'

interface LayoutProps {
  children?: ReactNode
}

// ナビゲーションメニュー項目の型
interface NavItem {
  path: string
  label: string
  icon: LucideIcon
  requiredRole?: UserRole | UserRole[]
}

// ナビゲーションメニュー項目
const navItems: NavItem[] = [
  { path: '/', label: 'ダッシュボード', icon: Home },
  { path: '/teams', label: 'チーム管理', icon: Users, requiredRole: 'admin' },
  { path: '/schedule', label: '日程管理', icon: Calendar, requiredRole: 'admin' },
  { path: '/results', label: '試合結果入力', icon: ClipboardEdit, requiredRole: ['admin', 'venue_staff'] },
  { path: '/standings', label: '順位表', icon: Trophy },
  { path: '/reports', label: '報告書出力', icon: FileText, requiredRole: 'admin' },
  { path: '/settings', label: '設定', icon: Settings, requiredRole: 'admin' },
]

/**
 * ユーザーの権限に応じてナビゲーション項目を表示するかチェック
 */
function canAccessNavItem(item: NavItem, userRole?: UserRole): boolean {
  if (!item.requiredRole) return true
  if (!userRole) return false
  if (userRole === 'admin') return true

  const roles = Array.isArray(item.requiredRole) ? item.requiredRole : [item.requiredRole]
  return roles.includes(userRole)
}

/**
 * 権限バッジコンポーネント
 */
function RoleBadge({ role }: { role: UserRole }) {
  const config = {
    admin: { label: '管理者', className: 'bg-red-100 text-red-700' },
    venue_staff: { label: '会場担当', className: 'bg-blue-100 text-blue-700' },
    viewer: { label: '閲覧者', className: 'bg-gray-100 text-gray-700' },
  }
  const { label, className } = config[role] || config.viewer

  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', className)}>
      {label}
    </span>
  )
}

/**
 * 共通レイアウトコンポーネント
 * サイドバーナビゲーションとメインコンテンツエリア
 */
function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const { isAuthenticated, user, logout } = useAuthStore()

  // リアルタイム更新を有効化（WebSocket接続 + React Query連携）
  useRealtimeUpdates({ showNotifications: true })


  const { setCurrentTournament } = useAppStore()

  // 大会情報を取得してグローバルストアに保存
  // 他のコンポーネント（Dashboard, Sidebar, Settings等）と同期するため
  const { data: tournament } = useQuery({
    queryKey: ['tournament', 1], // TODO: ID動的化
    queryFn: async () => {
      const { data } = await api.get<Tournament>('/tournaments/1')
      return data
    },
  })

  // ストアの状態を更新
  useEffect(() => {
    if (tournament) {
      setCurrentTournament(tournament)
    }
  }, [tournament, setCurrentTournament])

  /**
   * ログアウト処理
   */
  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* モバイルメニューボタン */}
      <button
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md"
        aria-label="メニューを開く"
      >
        {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* オーバーレイ（モバイル時） */}
      {isSidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* サイドバー */}
      <aside
        className={clsx(
          'fixed top-0 left-0 z-40 h-screen w-64 bg-white border-r border-gray-200 transition-transform duration-300',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* ロゴ・タイトル */}
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Trophy className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg text-gray-900">浦和カップ</span>
          </Link>
        </div>

        {/* ユーザー情報（認証済みの場合） */}
        {isAuthenticated && user && (
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                {user.role === 'admin' ? (
                  <Shield className="w-5 h-5 text-red-600" />
                ) : (
                  <User className="w-5 h-5 text-gray-600" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{user.displayName}</p>
                <RoleBadge role={user.role} />
              </div>
            </div>
          </div>
        )}

        {/* ナビゲーションメニュー */}
        <nav className="p-4 space-y-1">
          {navItems
            .filter((item) => canAccessNavItem(item, user?.role))
            .map((item) => {
              const isActive = location.pathname === item.path
              const Icon = item.icon

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsSidebarOpen(false)}
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  )}
                >
                  <Icon
                    size={20}
                    className={isActive ? 'text-primary-600' : 'text-gray-400'}
                  />
                  {item.label}
                </Link>
              )
            })}
        </nav>

        {/* ログイン/ログアウトボタン */}
        <div className="absolute bottom-28 left-0 right-0 p-4">
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100 hover:text-gray-900 font-medium transition-colors"
            >
              <LogOut size={20} />
              ログアウト
            </button>
          ) : (
            <Link
              to="/login"
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-primary-600 text-white hover:bg-primary-700 font-medium transition-colors"
            >
              <LogIn size={20} />
              ログイン
            </Link>
          )}
        </div>

        {/* オフラインインジケーター & リアルタイム接続状態 */}
        <div className="absolute bottom-16 left-0 right-0 px-4 mb-2 space-y-2">
          <OfflineIndicator showDetails />
          <div className="flex items-center justify-center gap-2">
            <Wifi size={14} className="text-gray-400" />
            <ConnectionStatus compact={false} />
          </div>
        </div>

        {/* フッター情報 */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            浦和カップ トーナメント管理システム
          </p>
          <p className="text-xs text-gray-400 text-center mt-1">
            Version 1.0.0
          </p>
        </div>
      </aside>

      {/* メインコンテンツ */}
      <main className="lg:ml-64 min-h-screen">
        <div className="p-4 lg:p-8">{children || <Outlet />}</div>
      </main>
    </div>
  )
}

export default Layout
