/**
 * オフラインインジケーター
 *
 * オフライン状態と同期状態を表示するコンポーネント
 */

import React from 'react';
import { Wifi, WifiOff, RefreshCw, AlertTriangle, Check } from 'lucide-react';
import { useOnlineStatus, useSyncState } from '@/hooks/usePWA';
import { cn } from '@/utils/cn';

interface OfflineIndicatorProps {
  className?: string;
  /** 詳細表示モード */
  showDetails?: boolean;
}

export const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({
  className,
  showDetails = false,
}) => {
  const isOnline = useOnlineStatus();
  const { isSyncing, pendingCount, conflictCount, lastSyncAt, error, sync } = useSyncState();

  // オンラインで同期待ちがない場合は何も表示しない（シンプルモード）
  if (!showDetails && isOnline && pendingCount === 0 && conflictCount === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-2 rounded-lg text-sm',
        isOnline
          ? pendingCount > 0 || conflictCount > 0
            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
            : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
        className
      )}
    >
      {/* 接続状態アイコン */}
      {isOnline ? (
        <Wifi className="w-4 h-4" />
      ) : (
        <WifiOff className="w-4 h-4" />
      )}

      {/* ステータステキスト */}
      <div className="flex-1">
        {!isOnline ? (
          <span className="font-medium">オフライン</span>
        ) : isSyncing ? (
          <span className="flex items-center gap-1">
            <RefreshCw className="w-3 h-3 animate-spin" />
            同期中...
          </span>
        ) : pendingCount > 0 ? (
          <span>
            {pendingCount}件の変更が同期待ち
          </span>
        ) : conflictCount > 0 ? (
          <span className="flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            {conflictCount}件の競合あり
          </span>
        ) : (
          <span className="flex items-center gap-1">
            <Check className="w-3 h-3" />
            同期済み
          </span>
        )}

        {/* 詳細情報 */}
        {showDetails && lastSyncAt && (
          <div className="text-xs opacity-75 mt-0.5">
            最終同期: {formatTimeAgo(lastSyncAt)}
          </div>
        )}

        {/* エラー表示 */}
        {error && (
          <div className="text-xs text-red-600 dark:text-red-400 mt-0.5">
            {error}
          </div>
        )}
      </div>

      {/* 同期ボタン */}
      {isOnline && pendingCount > 0 && !isSyncing && (
        <button
          onClick={() => sync()}
          className="p-1 rounded hover:bg-black/10 transition-colors"
          title="今すぐ同期"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

/**
 * 経過時間を日本語でフォーマット
 */
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);

  if (diffSec < 60) {
    return 'たった今';
  } else if (diffMin < 60) {
    return `${diffMin}分前`;
  } else if (diffHour < 24) {
    return `${diffHour}時間前`;
  } else {
    return date.toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}

export default OfflineIndicator;
