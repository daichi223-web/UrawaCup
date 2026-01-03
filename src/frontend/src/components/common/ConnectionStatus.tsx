/**
 * WebSocket接続状態インジケーター
 *
 * リアルタイム更新の接続状態を視覚的に表示
 */

import React from 'react';
import { useConnectionStatus } from '@/hooks/useRealtimeUpdates';

interface ConnectionStatusProps {
  /** コンパクト表示（アイコンのみ） */
  compact?: boolean;
  /** クリック時に再接続を試行 */
  showReconnect?: boolean;
  /** カスタムクラス */
  className?: string;
}

/**
 * 接続状態のバッジカラー
 */
function getStatusColor(isConnected: boolean, isConnecting: boolean, isReconnecting: boolean) {
  if (isConnected) return 'bg-green-500';
  if (isConnecting || isReconnecting) return 'bg-yellow-500';
  return 'bg-red-500';
}

/**
 * 接続状態のラベル
 */
function getStatusLabel(isConnected: boolean, isConnecting: boolean, isReconnecting: boolean) {
  if (isConnected) return '接続中';
  if (isConnecting) return '接続中...';
  if (isReconnecting) return '再接続中...';
  return '切断';
}

/**
 * 接続状態インジケーターコンポーネント
 */
export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  compact = false,
  showReconnect = true,
  className = '',
}) => {
  const { isConnected, isConnecting, isReconnecting, connectionCount, reconnect } =
    useConnectionStatus();

  const statusColor = getStatusColor(isConnected, isConnecting, isReconnecting);
  const statusLabel = getStatusLabel(isConnected, isConnecting, isReconnecting);

  // 切断時のクリックで再接続
  const handleClick = () => {
    if (!isConnected && !isConnecting && !isReconnecting && showReconnect) {
      reconnect();
    }
  };

  if (compact) {
    return (
      <div
        className={`relative inline-flex items-center ${className}`}
        title={`リアルタイム接続: ${statusLabel}${isConnected ? ` (${connectionCount}人接続中)` : ''}`}
        onClick={handleClick}
        role={!isConnected && showReconnect ? 'button' : undefined}
        style={{ cursor: !isConnected && showReconnect ? 'pointer' : 'default' }}
      >
        <span
          className={`inline-block h-2.5 w-2.5 rounded-full ${statusColor} ${
            isConnecting || isReconnecting ? 'animate-pulse' : ''
          }`}
        />
      </div>
    );
  }

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
        isConnected
          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
          : isConnecting || isReconnecting
            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      } ${!isConnected && showReconnect ? 'cursor-pointer hover:opacity-80' : ''} ${className}`}
      onClick={handleClick}
      role={!isConnected && showReconnect ? 'button' : undefined}
    >
      <span
        className={`inline-block h-2 w-2 rounded-full ${statusColor} ${
          isConnecting || isReconnecting ? 'animate-pulse' : ''
        }`}
      />
      <span>{statusLabel}</span>
      {isConnected && connectionCount > 0 && (
        <span className="text-gray-500 dark:text-gray-400">({connectionCount})</span>
      )}
      {!isConnected && !isConnecting && !isReconnecting && showReconnect && (
        <span className="ml-1 text-xs underline">クリックで再接続</span>
      )}
    </div>
  );
};

export default ConnectionStatus;
