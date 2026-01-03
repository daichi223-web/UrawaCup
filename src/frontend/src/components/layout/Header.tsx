import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Menu,
  X,
  Bell,
  User,
  LogOut,
  Settings,
  Trophy,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAppStore } from '@/stores/appStore'
import { useAuthStore } from '@/stores/authStore'

interface HeaderProps {
  isSidebarOpen: boolean
  onToggleSidebar: () => void
}

/**
 * ヘッダーコンポーネント
 * モバイルメニュー、通知、ユーザーメニューを含む
 */
export function Header({ isSidebarOpen, onToggleSidebar }: HeaderProps) {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const { isOnline, currentTournament } = useAppStore()
  const { user, logout, isAuthenticated } = useAuthStore()

  const handleLogout = () => {
    logout()
    setIsUserMenuOpen(false)
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-white border-b border-gray-200 lg:pl-64">
      <div className="flex items-center justify-between h-full px-4">
        {/* 左側: モバイルメニューボタン + タイトル */}
        <div className="flex items-center gap-4">
          {/* モバイルメニューボタン */}
          <button
            onClick={onToggleSidebar}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label={isSidebarOpen ? 'メニューを閉じる' : 'メニューを開く'}
          >
            {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>

          {/* モバイル用ロゴ */}
          <Link to="/" className="flex items-center gap-2 lg:hidden">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Trophy className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg text-gray-900 truncate max-w-[200px] lg:max-w-md">
              {currentTournament?.shortName || currentTournament?.name || '浦和カップ'}
            </span>
          </Link>

          {/* デスクトップ用: 現在の大会名 */}
          {/* デスクトップ用: 現在の大会名 (タイトルに統合されたため削除) */}
        </div>

        {/* 右側: 通知・ユーザーメニュー */}
        <div className="flex items-center gap-3">
          {/* オンライン/オフライン状態表示 */}
          <div
            className={clsx(
              'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
              isOnline
                ? 'bg-green-100 text-green-700'
                : 'bg-yellow-100 text-yellow-700'
            )}
          >
            {isOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
            <span className="hidden sm:inline">
              {isOnline ? 'オンライン' : 'オフライン'}
            </span>
          </div>

          {/* 通知ベル */}
          <button
            className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="通知"
          >
            <Bell size={20} className="text-gray-600" />
            {/* 未読通知バッジ（サンプル） */}
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          </button>

          {/* ユーザーメニュー */}
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="ユーザーメニュー"
              aria-expanded={isUserMenuOpen}
            >
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <User size={18} className="text-primary-600" />
              </div>
              <span className="hidden sm:block text-sm font-medium text-gray-700">
                {isAuthenticated ? user?.displayName : 'ゲスト'}
              </span>
            </button>

            {/* ドロップダウンメニュー */}
            {isUserMenuOpen && (
              <>
                {/* オーバーレイ */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setIsUserMenuOpen(false)}
                />

                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                  {isAuthenticated ? (
                    <>
                      <div className="px-4 py-2 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900">
                          {user?.displayName}
                        </p>
                        <p className="text-xs text-gray-500">
                          {user?.role === 'admin' && '管理者'}
                          {user?.role === 'venue_staff' && '会場担当者'}
                          {user?.role === 'viewer' && '閲覧者'}
                        </p>
                      </div>
                      <Link
                        to="/settings"
                        className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setIsUserMenuOpen(false)}
                      >
                        <Settings size={16} />
                        設定
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        <LogOut size={16} />
                        ログアウト
                      </button>
                    </>
                  ) : (
                    <Link
                      to="/login"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <User size={16} />
                      ログイン
                    </Link>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
