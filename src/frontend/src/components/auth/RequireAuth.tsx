import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import type { UserRole } from '@shared/types'

/**
 * 認証が必要なルートを保護するコンポーネント
 */
interface RequireAuthProps {
  children: React.ReactNode
  /** 必要な権限レベル（オプション） */
  requiredRole?: UserRole | UserRole[]
}

/**
 * 認証必須ルート用ラッパーコンポーネント
 *
 * - 未認証の場合はログインページにリダイレクト
 * - 権限が不足している場合はダッシュボードにリダイレクト
 */
export function RequireAuth({ children, requiredRole }: RequireAuthProps) {
  const { isAuthenticated, user } = useAuthStore()
  const location = useLocation()

  // 未認証の場合はログインページへ
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  // 権限チェックが必要な場合
  if (requiredRole && user) {
    const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole]

    // 管理者は全ての権限を持つ
    if (user.role !== 'admin' && !roles.includes(user.role)) {
      return <Navigate to="/" replace />
    }
  }

  return <>{children}</>
}

/**
 * 管理者専用ルート用ラッパーコンポーネント
 */
export function RequireAdmin({ children }: { children: React.ReactNode }) {
  return <RequireAuth requiredRole="admin">{children}</RequireAuth>
}

/**
 * 会場担当者以上の権限が必要なルート用ラッパーコンポーネント
 */
export function RequireVenueManager({ children }: { children: React.ReactNode }) {
  return <RequireAuth requiredRole={['admin', 'venue_staff']}>{children}</RequireAuth>
}

export default RequireAuth
