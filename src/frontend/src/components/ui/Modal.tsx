import { ReactNode, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { clsx } from 'clsx'
import { X } from 'lucide-react'

/**
 * モーダルのサイズ
 */
type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full'

/**
 * モーダルのプロパティ
 */
interface ModalProps {
  /** 表示状態 */
  isOpen: boolean
  /** 閉じる関数 */
  onClose: () => void
  /** タイトル */
  title?: string
  /** 子要素 */
  children: ReactNode
  /** サイズ */
  size?: ModalSize
  /** 閉じるボタン非表示 */
  hideCloseButton?: boolean
  /** オーバーレイクリックで閉じない */
  preventOverlayClose?: boolean
  /** ESCキーで閉じない */
  preventEscClose?: boolean
  /** フッター */
  footer?: ReactNode
}

// サイズごとのスタイル
const sizeStyles: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-4xl',
}

/**
 * モーダルコンポーネント
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  hideCloseButton = false,
  preventOverlayClose = false,
  preventEscClose = false,
  footer,
}: ModalProps) {
  // ESCキーで閉じる
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !preventEscClose) {
        onClose()
      }
    },
    [onClose, preventEscClose]
  )

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [isOpen, handleKeyDown])

  // オーバーレイクリック
  const handleOverlayClick = () => {
    if (!preventOverlayClose) {
      onClose()
    }
  }

  if (!isOpen) return null

  return createPortal(
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* オーバーレイ */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={handleOverlayClick}
        aria-hidden="true"
      />

      {/* モーダルコンテナ */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className={clsx(
            'relative w-full bg-white rounded-lg shadow-xl transform transition-all',
            sizeStyles[size]
          )}
          role="dialog"
          aria-modal="true"
          aria-labelledby={title ? 'modal-title' : undefined}
          onClick={(e) => e.stopPropagation()}
        >
          {/* ヘッダー */}
          {(title || !hideCloseButton) && (
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
              {title && (
                <h2
                  id="modal-title"
                  className="text-lg font-semibold text-gray-900"
                >
                  {title}
                </h2>
              )}
              {!hideCloseButton && (
                <button
                  onClick={onClose}
                  className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  aria-label="閉じる"
                >
                  <X size={20} />
                </button>
              )}
            </div>
          )}

          {/* 本文 */}
          <div className="p-4">{children}</div>

          {/* フッター */}
          {footer && (
            <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-gray-200 bg-gray-50 rounded-b-lg">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}

/**
 * 確認モーダル
 */
interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  confirmVariant?: 'primary' | 'danger'
  isLoading?: boolean
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = '確認',
  cancelLabel = 'キャンセル',
  confirmVariant = 'primary',
  isLoading = false,
}: ConfirmModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={clsx(
              'px-4 py-2 text-sm font-medium text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50',
              confirmVariant === 'danger'
                ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                : 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500'
            )}
          >
            {isLoading ? '処理中...' : confirmLabel}
          </button>
        </>
      }
    >
      <p className="text-gray-600">{message}</p>
    </Modal>
  )
}
