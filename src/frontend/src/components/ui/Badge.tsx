import { ReactNode, HTMLAttributes } from 'react'
import { clsx } from 'clsx'

/**
 * バッジのバリアント
 */
type BadgeVariant =
  | 'default'
  | 'primary'
  | 'success'
  | 'warning'
  | 'danger'
  | 'group-a'
  | 'group-b'
  | 'group-c'
  | 'group-d'

/**
 * バッジのサイズ
 */
type BadgeSize = 'sm' | 'md' | 'lg'

/**
 * バッジのプロパティ
 */
interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode
  /** バリアント */
  variant?: BadgeVariant
  /** サイズ */
  size?: BadgeSize
  /** ドット付き */
  withDot?: boolean
  /** ドットの色 */
  dotColor?: string
}

// バリアントごとのスタイル
const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-800',
  primary: 'bg-primary-100 text-primary-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  danger: 'bg-red-100 text-red-800',
  'group-a': 'bg-red-100 text-red-800',
  'group-b': 'bg-blue-100 text-blue-800',
  'group-c': 'bg-green-100 text-green-800',
  'group-d': 'bg-yellow-100 text-yellow-800',
}

// サイズごとのスタイル
const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-1.5 py-0.5 text-xs',
  md: 'px-2 py-0.5 text-xs',
  lg: 'px-2.5 py-1 text-sm',
}

/**
 * バッジコンポーネント
 */
export function Badge({
  children,
  className,
  variant = 'default',
  size = 'md',
  withDot = false,
  dotColor,
  ...props
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {withDot && (
        <span
          className={clsx(
            'w-1.5 h-1.5 rounded-full mr-1.5',
            dotColor || 'bg-current'
          )}
        />
      )}
      {children}
    </span>
  )
}

/**
 * グループバッジ（A〜Dグループ用）
 */
export function GroupBadge({ group }: { group: 'A' | 'B' | 'C' | 'D' }) {
  const variant = `group-${group.toLowerCase()}` as BadgeVariant
  return (
    <Badge variant={variant} size="sm">
      {group}組
    </Badge>
  )
}

/**
 * ステータスバッジ（試合状態用）
 */
export function MatchStatusBadge({
  status,
}: {
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
}) {
  const config: Record<
    typeof status,
    { label: string; variant: BadgeVariant; withDot: boolean; dotColor?: string }
  > = {
    scheduled: { label: '予定', variant: 'default', withDot: true, dotColor: 'bg-gray-400' },
    in_progress: { label: '試合中', variant: 'warning', withDot: true, dotColor: 'bg-yellow-500' },
    completed: { label: '終了', variant: 'success', withDot: true, dotColor: 'bg-green-500' },
    cancelled: { label: '中止', variant: 'danger', withDot: true, dotColor: 'bg-red-500' },
  }

  const { label, variant, withDot, dotColor } = config[status]

  return (
    <Badge variant={variant} size="sm" withDot={withDot} dotColor={dotColor}>
      {label}
    </Badge>
  )
}

/**
 * 承認ステータスバッジ
 */
export function ApprovalStatusBadge({
  status,
}: {
  status: 'pending' | 'approved' | 'rejected' | undefined | null
}) {
  if (!status) return null

  const config: Record<
    'pending' | 'approved' | 'rejected',
    { label: string; variant: BadgeVariant; withDot: boolean; dotColor?: string }
  > = {
    pending: { label: '承認待ち', variant: 'warning', withDot: true, dotColor: 'bg-yellow-500' },
    approved: { label: '承認済み', variant: 'success', withDot: true, dotColor: 'bg-green-500' },
    rejected: { label: '却下', variant: 'danger', withDot: true, dotColor: 'bg-red-500' },
  }

  const { label, variant, withDot, dotColor } = config[status]

  return (
    <Badge variant={variant} size="sm" withDot={withDot} dotColor={dotColor}>
      {label}
    </Badge>
  )
}

/**
 * 承認待ちカウントバッジ（ナビゲーション用）
 */
export function PendingApprovalCountBadge({ count }: { count: number }) {
  if (count <= 0) return null

  return (
    <span className="inline-flex items-center justify-center min-w-5 h-5 px-1.5 text-xs font-bold text-white bg-red-500 rounded-full">
      {count > 99 ? '99+' : count}
    </span>
  )
}
