/**
 * リアルタイム更新フック
 *
 * WebSocketとReact Queryを連携し、サーバーからの更新通知を
 * 受信したときに自動的にデータを再取得する
 */

import { useCallback, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  useWebSocket,
  WebSocketMessage,
  MatchUpdatePayload,
  StandingUpdatePayload,
  ApprovalUpdatePayload,
  ConnectionState,
} from './useWebSocket';

// トースト通知の設定
const TOAST_DURATION = 4000;

// 通知メッセージの生成
function getMatchUpdateMessage(payload: MatchUpdatePayload): string {
  switch (payload.action) {
    case 'score_updated':
      return `試合結果が更新されました (試合ID: ${payload.match_id})`;
    case 'approved':
      return `試合結果が承認されました (試合ID: ${payload.match_id})`;
    case 'rejected':
      return `試合結果が却下されました (試合ID: ${payload.match_id})`;
    case 'created':
      return `新しい試合が作成されました`;
    case 'deleted':
      return `試合が削除されました`;
    default:
      return `試合情報が更新されました`;
  }
}

function getStandingUpdateMessage(payload: StandingUpdatePayload): string {
  return `順位表が更新されました (グループ${payload.group_id})`;
}

function getApprovalUpdateMessage(payload: ApprovalUpdatePayload): string {
  switch (payload.approval_status) {
    case 'approved':
      return `試合結果が${payload.approved_by_name || '管理者'}により承認されました`;
    case 'rejected':
      return `試合結果が却下されました。修正が必要です`;
    case 'pending':
      return `試合結果が承認待ちになりました`;
    default:
      return `承認状態が更新されました`;
  }
}

// フックのオプション
export interface UseRealtimeUpdatesOptions {
  // 通知を表示するかどうか
  showNotifications?: boolean;
  // 特定の大会のみを監視
  tournamentId?: number;
  // 特定のグループのみを監視
  groupId?: string;
}

// フックの戻り値
export interface UseRealtimeUpdatesReturn {
  connectionState: ConnectionState;
  connectionCount: number;
  reconnect: () => void;
}

/**
 * リアルタイム更新フック
 *
 * @param options オプション設定
 * @returns 接続状態と制御関数
 */
export function useRealtimeUpdates(
  options: UseRealtimeUpdatesOptions = {}
): UseRealtimeUpdatesReturn {
  const { showNotifications = true, tournamentId, groupId } = options;
  const queryClient = useQueryClient();

  // WebSocketメッセージ受信時の処理
  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      switch (message.type) {
        case 'CONNECTED':
          console.log('リアルタイム接続確立:', message.payload.message);
          break;

        case 'MATCH_UPDATE': {
          const matchPayload = message.payload as MatchUpdatePayload;

          // フィルタリング（指定された場合）
          if (tournamentId && matchPayload.tournament_id !== tournamentId) {
            return;
          }

          // React Queryのキャッシュを無効化
          queryClient.invalidateQueries({ queryKey: ['matches'] });
          queryClient.invalidateQueries({ queryKey: ['match', matchPayload.match_id] });

          // 順位表も更新（予選リーグの場合）
          if (matchPayload.group_id) {
            queryClient.invalidateQueries({
              queryKey: ['standings', matchPayload.tournament_id],
            });
            queryClient.invalidateQueries({
              queryKey: ['standings', matchPayload.tournament_id, matchPayload.group_id],
            });
          }

          // 通知を表示
          if (showNotifications) {
            toast.success(getMatchUpdateMessage(matchPayload), {
              duration: TOAST_DURATION,
              icon: '⚽',
            });
          }
          break;
        }

        case 'STANDING_UPDATE': {
          const standingPayload = message.payload as StandingUpdatePayload;

          // フィルタリング（指定された場合）
          if (tournamentId && standingPayload.tournament_id !== tournamentId) {
            return;
          }
          if (groupId && standingPayload.group_id !== groupId) {
            return;
          }

          // React Queryのキャッシュを無効化
          queryClient.invalidateQueries({
            queryKey: ['standings', standingPayload.tournament_id],
          });
          queryClient.invalidateQueries({
            queryKey: ['standings', standingPayload.tournament_id, standingPayload.group_id],
          });

          // 通知を表示
          if (showNotifications) {
            toast.success(getStandingUpdateMessage(standingPayload), {
              duration: TOAST_DURATION,
              icon: '📊',
            });
          }
          break;
        }

        case 'APPROVAL_UPDATE': {
          const approvalPayload = message.payload as ApprovalUpdatePayload;

          // フィルタリング（指定された場合）
          if (tournamentId && approvalPayload.tournament_id !== tournamentId) {
            return;
          }

          // React Queryのキャッシュを無効化
          queryClient.invalidateQueries({ queryKey: ['matches'] });
          queryClient.invalidateQueries({ queryKey: ['match', approvalPayload.match_id] });
          queryClient.invalidateQueries({ queryKey: ['pending-matches'] });

          // 通知を表示
          if (showNotifications) {
            const toastFn =
              approvalPayload.approval_status === 'rejected' ? toast.error : toast.success;
            toastFn(getApprovalUpdateMessage(approvalPayload), {
              duration: TOAST_DURATION,
              icon: approvalPayload.approval_status === 'approved' ? '✅' : '⚠️',
            });
          }
          break;
        }

        case 'MATCH_LOCKED': {
          // 試合のロック通知（オプション）
          console.log('試合がロックされました:', message.payload);
          queryClient.invalidateQueries({ queryKey: ['match', message.payload.match_id] });
          break;
        }

        case 'MATCH_UNLOCKED': {
          // 試合のロック解除通知（オプション）
          console.log('試合のロックが解除されました:', message.payload);
          queryClient.invalidateQueries({ queryKey: ['match', message.payload.match_id] });
          break;
        }

        default:
          console.log('未知のWebSocketメッセージ:', message);
      }
    },
    [queryClient, showNotifications, tournamentId, groupId]
  );

  // WebSocket接続
  const { connectionState, connectionCount, reconnect } = useWebSocket(handleMessage);

  // 接続状態の変化をログ
  useEffect(() => {
    if (connectionState === 'connected') {
      console.log(`リアルタイム更新: 接続中 (${connectionCount}クライアント接続)`);
    } else if (connectionState === 'disconnected') {
      console.log('リアルタイム更新: 切断');
    } else if (connectionState === 'reconnecting') {
      console.log('リアルタイム更新: 再接続中...');
    }
  }, [connectionState, connectionCount]);

  return {
    connectionState,
    connectionCount,
    reconnect,
  };
}

/**
 * 接続状態インジケーターコンポーネント用のフック
 */
export function useConnectionStatus() {
  const { connectionState, connectionCount, reconnect } = useWebSocket();

  return {
    isConnected: connectionState === 'connected',
    isConnecting: connectionState === 'connecting',
    isReconnecting: connectionState === 'reconnecting',
    connectionCount,
    reconnect,
  };
}
