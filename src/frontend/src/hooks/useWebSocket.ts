/**
 * WebSocket接続管理フック
 *
 * リアルタイム更新機能を提供:
 * - 試合結果更新通知 (MATCH_UPDATE)
 * - 順位表更新通知 (STANDING_UPDATE)
 * - 承認状態更新通知 (APPROVAL_UPDATE)
 * - 自動再接続（エクスポネンシャルバックオフ）
 * - 接続状態管理
 */

import { useEffect, useRef, useState, useCallback } from 'react';

// 再接続設定
const INITIAL_RECONNECT_INTERVAL = 1000;  // 初期再接続間隔（1秒）
const MAX_RECONNECT_INTERVAL = 30000;     // 最大再接続間隔（30秒）
const RECONNECT_MULTIPLIER = 1.5;         // 再接続間隔の増加率
const HEARTBEAT_INTERVAL = 30000;         // ハートビート間隔（30秒）
const MAX_RECONNECT_ATTEMPTS = 5;         // 最大再接続試行回数

// WebSocketイベントタイプ
export type WebSocketEventType =
  | 'CONNECTED'
  | 'MATCH_UPDATE'
  | 'STANDING_UPDATE'
  | 'APPROVAL_UPDATE'
  | 'MATCH_LOCKED'
  | 'MATCH_UNLOCKED';

// 試合更新ペイロード
export interface MatchUpdatePayload {
  match_id: number;
  tournament_id: number;
  action?: 'score_updated' | 'created' | 'deleted' | 'approved' | 'rejected';
  home_score?: number;
  away_score?: number;
  group_id?: string;
  status?: string;
  timestamp?: string;
}

// 順位表更新ペイロード
export interface StandingUpdatePayload {
  tournament_id: number;
  group_id: string;
  reason?: string;
  timestamp?: string;
}

// 承認更新ペイロード
export interface ApprovalUpdatePayload {
  match_id: number;
  tournament_id: number;
  approval_status: 'pending' | 'approved' | 'rejected';
  approved_by_name?: string;
  timestamp?: string;
}

// 接続確認ペイロード
export interface ConnectedPayload {
  message: string;
  timestamp: string;
  connection_count: number;
}

// WebSocketメッセージ型
export type WebSocketMessage =
  | { type: 'CONNECTED'; payload: ConnectedPayload }
  | { type: 'MATCH_UPDATE'; payload: MatchUpdatePayload }
  | { type: 'STANDING_UPDATE'; payload: StandingUpdatePayload }
  | { type: 'APPROVAL_UPDATE'; payload: ApprovalUpdatePayload }
  | { type: 'MATCH_LOCKED'; payload: { match_id: number; locked_by: string } }
  | { type: 'MATCH_UNLOCKED'; payload: { match_id: number } };

// 接続状態
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

// フックの戻り値
export interface UseWebSocketReturn {
  connectionState: ConnectionState;
  connectionCount: number;
  lastMessage: WebSocketMessage | null;
  reconnect: () => void;
}

// WebSocketのURLを取得
function getWebSocketUrl(): string {
  // 環境変数からURLを取得
  const wsBaseUrl = import.meta.env.VITE_WS_URL;

  // 絶対URLの場合（ws:// または wss:// で始まる）
  if (wsBaseUrl && (wsBaseUrl.startsWith('ws://') || wsBaseUrl.startsWith('wss://'))) {
    return wsBaseUrl;
  }

  // 相対パスまたは未設定の場合は、現在のホストを使用（Viteプロキシ経由）
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const path = wsBaseUrl || '/ws';
  return `${protocol}//${window.location.host}${path}`;
}

/**
 * WebSocket接続管理フック
 *
 * @param onMessage メッセージ受信時のコールバック
 * @returns 接続状態と制御関数
 */
export function useWebSocket(
  onMessage?: (message: WebSocketMessage) => void
): UseWebSocketReturn {
  const ws = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectIntervalRef = useRef(INITIAL_RECONNECT_INTERVAL);
  const reconnectAttemptsRef = useRef(0);

  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [connectionCount, setConnectionCount] = useState(0);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  // コールバックの参照を最新に保つ
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  // ハートビート送信
  const sendHeartbeat = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify({ type: 'ping' }));
      } catch (e) {
        console.warn('ハートビート送信エラー:', e);
      }
    }
  }, []);

  // ハートビート開始
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    heartbeatIntervalRef.current = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);
  }, [sendHeartbeat]);

  // ハートビート停止
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // 接続処理
  const connect = useCallback(() => {
    // 既存の接続があれば閉じる
    if (ws.current) {
      ws.current.close();
    }

    // 再接続タイムアウトをクリア
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setConnectionState('connecting');
    const wsUrl = getWebSocketUrl();
    console.log(`WebSocket接続開始: ${wsUrl}`);

    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket接続成功');
        setConnectionState('connected');
        reconnectIntervalRef.current = INITIAL_RECONNECT_INTERVAL; // 再接続間隔をリセット
        reconnectAttemptsRef.current = 0; // 再接続試行回数をリセット
        startHeartbeat();
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage;
          setLastMessage(data);

          // 接続確認メッセージの場合、接続数を更新
          if (data.type === 'CONNECTED') {
            setConnectionCount(data.payload.connection_count);
          }

          // コールバックを呼び出し
          if (onMessageRef.current) {
            onMessageRef.current(data);
          }
        } catch (e) {
          console.error('WebSocketメッセージのパースエラー:', e);
        }
      };

      socket.onclose = (event) => {
        console.log(`WebSocket切断: code=${event.code}, reason=${event.reason}`);
        setConnectionState('disconnected');
        stopHeartbeat();

        // 正常終了でない場合は再接続（回数制限あり）
        if (event.code !== 1000) {
          reconnectAttemptsRef.current += 1;

          if (reconnectAttemptsRef.current > MAX_RECONNECT_ATTEMPTS) {
            console.log('最大再接続試行回数に達しました。WebSocket接続を停止します。');
            return;
          }

          setConnectionState('reconnecting');
          const nextInterval = Math.min(
            reconnectIntervalRef.current * RECONNECT_MULTIPLIER,
            MAX_RECONNECT_INTERVAL
          );
          console.log(`${reconnectIntervalRef.current}ms後に再接続します... (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectIntervalRef.current = nextInterval;
            connect();
          }, reconnectIntervalRef.current);
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocketエラー:', error);
        // oncloseで再接続処理が行われるので、ここでは何もしない
      };

      ws.current = socket;
    } catch (e) {
      console.error('WebSocket接続エラー:', e);
      setConnectionState('disconnected');
    }
  }, [startHeartbeat, stopHeartbeat]);

  // 手動再接続
  const reconnect = useCallback(() => {
    console.log('手動再接続を開始...');
    reconnectIntervalRef.current = INITIAL_RECONNECT_INTERVAL;
    connect();
  }, [connect]);

  // 初期接続とクリーンアップ
  useEffect(() => {
    connect();

    return () => {
      // クリーンアップ
      stopHeartbeat();

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (ws.current) {
        ws.current.close(1000, 'コンポーネントのアンマウント');
        ws.current = null;
      }
    };
  }, [connect, stopHeartbeat]);

  // オンライン/オフラインイベントの監視
  useEffect(() => {
    const handleOnline = () => {
      console.log('オンラインに復帰しました。WebSocket再接続...');
      reconnect();
    };

    const handleOffline = () => {
      console.log('オフラインになりました');
      setConnectionState('disconnected');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [reconnect]);

  return {
    connectionState,
    connectionCount,
    lastMessage,
    reconnect,
  };
}
