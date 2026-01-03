import { Link, useLocation } from 'react-router-dom'
import {
  Home,
  Users,
  Calendar,
  ClipboardEdit,
  Trophy,
  FileText,
  Settings,
  Layers,
  MapPin,
  UserCircle,
  ClipboardCheck,
  Ban,
  Award,
  LucideIcon,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuthStore } from '@/stores/authStore'
import { useAppStore } from '@/stores/appStore'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

// ナビゲーションメニュー項目の型
interface NavItem {
  path: string
  label: string
  icon: LucideIcon
  /** 表示に必要な権限（指定なしは全員） */
  roles?: Array<'admin' | 'venue_staff' | 'viewer'>
  /** メニューグループ */
  group: 'main' | 'management' | 'system'
}

// ナビゲーションメニュー項目
const navItems: NavItem[] = [
  // メイン機能
  { path: '/', label: 'ダッシュボード', icon: Home, group: 'main' },
  { path: '/results', label: '試合結果入力', icon: ClipboardEdit, group: 'main', roles: ['admin', 'venue_staff'] },
  { path: '/standings', label: '順位表', icon: Trophy, group: 'main' },
  { path: '/scorer-ranking', label: '得点ランキング', icon: Award, group: 'main' },
  { path: '/schedule', label: '日程管理', icon: Calendar, group: 'main' },
  { path: '/reports', label: '報告書出力', icon: FileText, group: 'main', roles: ['admin'] },
  { path: '/approval', label: '結果承認', icon: ClipboardCheck, group: 'main', roles: ['admin'] },

  // 管理機能
  { path: '/teams', label: 'チーム管理', icon: Users, group: 'management', roles: ['admin'] },
  { path: '/players', label: '選手管理', icon: UserCircle, group: 'management', roles: ['admin'] },
  { path: '/venues', label: '会場管理', icon: MapPin, group: 'management', roles: ['admin'] },
  { path: '/groups', label: 'グループ設定', icon: Layers, group: 'management', roles: ['admin'] },
  { path: '/exclusions', label: '対戦除外', icon: Ban, group: 'management', roles: ['admin'] },

  // システム
  { path: '/settings', label: '設定', icon: Settings, group: 'system', roles: ['admin'] },
]

// グループラベル
const groupLabels: Record<string, string> = {
  main: 'メイン',
  management: '管理',
  system: 'システム',
}

/**
 * サイドバーナビゲーションコンポーネント
 */
export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation()
  const { user, isAuthenticated } = useAuthStore()
  const { currentTournament } = useAppStore()

  // ユーザーの権限に基づいてメニュー項目をフィルタリング
  const filteredNavItems = navItems.filter((item) => {
    if (!item.roles) return true // 権限指定なしは全員表示
    if (!isAuthenticated || !user) return false
    return item.roles.includes(user.role)
  })

  // グループごとにメニュー項目を分類
  const groupedItems = filteredNavItems.reduce((acc, item) => {
    if (!acc[item.group]) {
      acc[item.group] = []
    }
    acc[item.group].push(item)
    return acc
  }, {} as Record<string, NavItem[]>)

  return (
    <>
      {/* オーバーレイ（モバイル時） */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* サイドバー本体 */}
      <aside
        className={clsx(
          'fixed top-0 left-0 z-40 h-screen w-64 bg-white border-r border-gray-200 transition-transform duration-300 flex flex-col',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* ロゴ・タイトル */}
        <div className="h-16 flex items-center px-6 border-b border-gray-200 flex-shrink-0">
          <Link to="/" className="flex items-center gap-2" onClick={onClose}>
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Trophy className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg text-gray-900 truncate" title={
              currentTournament
                ? (currentTournament.shortName || currentTournament.name || '浦和カップ')
                : '浦和カップ'
            }>
              {currentTournament
                ? (currentTournament.shortName || currentTournament.name || '浦和カップ')
                : '浦和カップ'}
            </span>
          </Link>
        </div>

        {/* ナビゲーションメニュー */}
        <nav className="flex-1 overflow-y-auto p-4 scrollbar-thin">
          {Object.entries(groupedItems).map(([group, items]) => (
            <div key={group} className="mb-6">
              {/* グループラベル */}
              <p className="px-4 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {groupLabels[group]}
              </p>

              {/* メニュー項目 */}
              <div className="space-y-1">
                {items.map((item) => {
                  const isActive = location.pathname === item.path
                  const Icon = item.icon

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className={clsx(
                        'flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-colors',
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
              </div>
            </div>
          ))}
        </nav>

        {/* フッター情報 */}
        <div className="flex-shrink-0 p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 px-4 py-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <p className="text-xs text-gray-500">
              浦和カップ トーナメント管理システム
            </p>
          </div>
          <p className="text-xs text-gray-400 text-center mt-1">
            Version 1.0.0
          </p>
        </div>
      </aside>
    </>
  )
}
