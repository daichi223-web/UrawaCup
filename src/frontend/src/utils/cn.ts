import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Tailwind CSS クラス名を結合するユーティリティ
 * clsx + tailwind-merge でクラス名の衝突を解決
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
