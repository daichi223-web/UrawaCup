import { forwardRef, SelectHTMLAttributes } from 'react'
import { clsx } from 'clsx'
import { ChevronDown } from 'lucide-react'

/**
 * セレクトオプションの型
 */
export interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
}

/**
 * セレクトのプロパティ
 */
interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  /** ラベル */
  label?: string
  /** エラーメッセージ */
  error?: string
  /** ヘルパーテキスト */
  helperText?: string
  /** オプション一覧 */
  options: SelectOption[]
  /** プレースホルダー */
  placeholder?: string
  /** フルwidth */
  fullWidth?: boolean
}

/**
 * 汎用セレクトコンポーネント
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      className,
      label,
      error,
      helperText,
      options,
      placeholder,
      fullWidth = true,
      id,
      ...props
    },
    ref
  ) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className={clsx(fullWidth ? 'w-full' : 'inline-block')}>
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={clsx(
              'block w-full px-3 py-2 pr-10 border rounded-lg shadow-sm appearance-none',
              'focus:outline-none focus:ring-2 focus:border-transparent',
              'transition-colors duration-200',
              'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
              error
                ? 'border-red-300 focus:ring-red-500'
                : 'border-gray-300 focus:ring-primary-500',
              className
            )}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${selectId}-error` : undefined}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-gray-400">
            <ChevronDown size={16} />
          </div>
        </div>
        {error && (
          <p id={`${selectId}-error`} className="mt-1 text-sm text-red-600">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p className="mt-1 text-sm text-gray-500">{helperText}</p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'
