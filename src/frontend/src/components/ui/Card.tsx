import { ReactNode, HTMLAttributes } from 'react'
import { clsx } from 'clsx'

/**
 * カードのプロパティ
 */
interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  /** パディングなし */
  noPadding?: boolean
}

/**
 * カードヘッダーのプロパティ
 */
interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  /** タイトル */
  title?: string
  /** 説明 */
  description?: string
  /** 右側のアクション */
  action?: ReactNode
}

/**
 * カード本体のプロパティ
 */
interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

/**
 * カードフッターのプロパティ
 */
interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

/**
 * カードコンポーネント
 */
export function Card({ children, className, noPadding, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-sm border border-gray-200',
        !noPadding && 'p-4',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

/**
 * カードヘッダーコンポーネント
 */
export function CardHeader({
  children,
  className,
  title,
  description,
  action,
  ...props
}: CardHeaderProps) {
  return (
    <div
      className={clsx(
        'flex items-center justify-between px-4 py-3 border-b border-gray-200',
        className
      )}
      {...props}
    >
      <div>
        {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
        {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
        {children}
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </div>
  )
}

/**
 * カード本体コンポーネント
 */
export function CardBody({ children, className, ...props }: CardBodyProps) {
  return (
    <div className={clsx('p-4', className)} {...props}>
      {children}
    </div>
  )
}

/**
 * カードフッターコンポーネント
 */
export function CardFooter({ children, className, ...props }: CardFooterProps) {
  return (
    <div
      className={clsx(
        'flex items-center justify-end gap-2 px-4 py-3 border-t border-gray-200 bg-gray-50 rounded-b-lg',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
