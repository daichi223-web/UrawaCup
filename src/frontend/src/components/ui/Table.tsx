import { ReactNode, HTMLAttributes, ThHTMLAttributes, TdHTMLAttributes } from 'react'
import { clsx } from 'clsx'

/**
 * テーブルのプロパティ
 */
interface TableProps extends HTMLAttributes<HTMLTableElement> {
  children: ReactNode
}

/**
 * テーブルヘッダーのプロパティ
 */
interface TableHeaderProps extends HTMLAttributes<HTMLTableSectionElement> {
  children: ReactNode
}

/**
 * テーブルボディのプロパティ
 */
interface TableBodyProps extends HTMLAttributes<HTMLTableSectionElement> {
  children: ReactNode
}

/**
 * テーブル行のプロパティ
 */
interface TableRowProps extends HTMLAttributes<HTMLTableRowElement> {
  children: ReactNode
  /** ホバーハイライト */
  hoverable?: boolean
  /** 選択状態 */
  selected?: boolean
}

/**
 * テーブルヘッダーセルのプロパティ
 */
interface TableHeadProps extends ThHTMLAttributes<HTMLTableCellElement> {
  children?: ReactNode
  /** ソート可能 */
  sortable?: boolean
  /** 現在のソート方向 */
  sortDirection?: 'asc' | 'desc' | null
  /** ソートクリック時のハンドラ */
  onSort?: () => void
}

/**
 * テーブルデータセルのプロパティ
 */
interface TableCellProps extends TdHTMLAttributes<HTMLTableCellElement> {
  children?: ReactNode
}

/**
 * テーブルコンポーネント
 */
export function Table({ children, className, ...props }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table
        className={clsx('min-w-full divide-y divide-gray-200', className)}
        {...props}
      >
        {children}
      </table>
    </div>
  )
}

/**
 * テーブルヘッダー
 */
export function TableHeader({ children, className, ...props }: TableHeaderProps) {
  return (
    <thead className={clsx('bg-gray-50', className)} {...props}>
      {children}
    </thead>
  )
}

/**
 * テーブルボディ
 */
export function TableBody({ children, className, ...props }: TableBodyProps) {
  return (
    <tbody
      className={clsx('bg-white divide-y divide-gray-200', className)}
      {...props}
    >
      {children}
    </tbody>
  )
}

/**
 * テーブル行
 */
export function TableRow({
  children,
  className,
  hoverable = true,
  selected = false,
  ...props
}: TableRowProps) {
  return (
    <tr
      className={clsx(
        hoverable && 'hover:bg-gray-50 transition-colors',
        selected && 'bg-primary-50',
        className
      )}
      {...props}
    >
      {children}
    </tr>
  )
}

/**
 * テーブルヘッダーセル
 */
export function TableHead({
  children,
  className,
  sortable = false,
  sortDirection,
  onSort,
  ...props
}: TableHeadProps) {
  const handleClick = () => {
    if (sortable && onSort) {
      onSort()
    }
  }

  return (
    <th
      className={clsx(
        'px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
        sortable && 'cursor-pointer hover:bg-gray-100 select-none',
        className
      )}
      onClick={handleClick}
      {...props}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortable && (
          <span className="inline-flex flex-col">
            <span
              className={clsx(
                'text-[8px] leading-none',
                sortDirection === 'asc' ? 'text-primary-600' : 'text-gray-300'
              )}
            >
              ▲
            </span>
            <span
              className={clsx(
                'text-[8px] leading-none',
                sortDirection === 'desc' ? 'text-primary-600' : 'text-gray-300'
              )}
            >
              ▼
            </span>
          </span>
        )}
      </div>
    </th>
  )
}

/**
 * テーブルデータセル
 */
export function TableCell({ children, className, ...props }: TableCellProps) {
  return (
    <td
      className={clsx('px-4 py-3 whitespace-nowrap text-sm text-gray-900', className)}
      {...props}
    >
      {children}
    </td>
  )
}

/**
 * 空データ表示
 */
export function TableEmpty({
  message = 'データがありません',
  colSpan,
}: {
  message?: string
  colSpan: number
}) {
  return (
    <tr>
      <td
        colSpan={colSpan}
        className="px-4 py-8 text-center text-gray-500 text-sm"
      >
        {message}
      </td>
    </tr>
  )
}
