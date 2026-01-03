"""
WebSocket接続管理モジュール

リアルタイム更新機能を提供:
- 試合結果更新通知 (MATCH_UPDATE)
- 順位表更新通知 (STANDING_UPDATE)
- 接続状態管理
"""

from typing import List, Dict, Any, Optional
from fastapi import WebSocket
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


# イベントタイプの定義
class WebSocketEventType:
    """WebSocketイベントタイプ"""
    MATCH_UPDATE = "MATCH_UPDATE"          # 試合結果が更新された
    STANDING_UPDATE = "STANDING_UPDATE"    # 順位表が更新された
    MATCH_LOCKED = "MATCH_LOCKED"          # 試合が編集ロックされた
    MATCH_UNLOCKED = "MATCH_UNLOCKED"      # 試合のロックが解除された
    APPROVAL_UPDATE = "APPROVAL_UPDATE"    # 承認状態が更新された
    CONNECTION_COUNT = "CONNECTION_COUNT"   # 接続数通知（管理用）


class ConnectionManager:
    """
    WebSocket接続管理クラス

    複数クライアントへのブロードキャスト、
    大会IDごとのチャンネル分け、ハートビート管理を提供
    """

    def __init__(self):
        # アクティブな接続リスト
        self.active_connections: List[WebSocket] = []
        # 大会ごとの接続を管理（将来の拡張用）
        self.tournament_connections: Dict[int, List[WebSocket]] = {}
        # 接続時刻の記録
        self.connection_times: Dict[WebSocket, datetime] = {}

    @property
    def connection_count(self) -> int:
        """現在の接続数を取得"""
        return len(self.active_connections)

    async def connect(self, websocket: WebSocket, tournament_id: Optional[int] = None):
        """
        クライアント接続時の処理

        Args:
            websocket: WebSocket接続
            tournament_id: 購読する大会ID（オプション）
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_times[websocket] = datetime.utcnow()

        # 大会固有のチャンネルに追加
        if tournament_id:
            if tournament_id not in self.tournament_connections:
                self.tournament_connections[tournament_id] = []
            self.tournament_connections[tournament_id].append(websocket)

        logger.info(f"WebSocket接続: 現在の接続数 = {self.connection_count}")

        # 接続確認メッセージを送信
        await self._send_safe(websocket, {
            "type": "CONNECTED",
            "payload": {
                "message": "WebSocket接続が確立されました",
                "timestamp": datetime.utcnow().isoformat(),
                "connection_count": self.connection_count
            }
        })

    def disconnect(self, websocket: WebSocket):
        """クライアント切断時の処理"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # 接続時刻を削除
        if websocket in self.connection_times:
            del self.connection_times[websocket]

        # 大会チャンネルからも削除
        for tournament_id in list(self.tournament_connections.keys()):
            if websocket in self.tournament_connections[tournament_id]:
                self.tournament_connections[tournament_id].remove(websocket)
                # 空になったチャンネルを削除
                if not self.tournament_connections[tournament_id]:
                    del self.tournament_connections[tournament_id]

        logger.info(f"WebSocket切断: 現在の接続数 = {self.connection_count}")

    async def _send_safe(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """
        安全にメッセージを送信（エラー時はFalseを返す）
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"WebSocket送信エラー: {e}")
            self.disconnect(websocket)
            return False

    async def broadcast(self, message: Dict[str, Any]):
        """
        全クライアントにメッセージを送信

        Args:
            message: 送信するメッセージ（type, payloadを含む辞書）
        """
        # タイムスタンプを追加
        if "payload" in message and isinstance(message["payload"], dict):
            message["payload"]["timestamp"] = datetime.utcnow().isoformat()

        # 送信タスクを並列実行
        tasks = []
        for connection in self.active_connections[:]:  # コピーを使用
            tasks.append(self._send_safe(connection, message))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.debug(f"ブロードキャスト完了: {success_count}/{len(tasks)} 成功")

    async def broadcast_to_tournament(self, tournament_id: int, message: Dict[str, Any]):
        """
        特定の大会を購読しているクライアントにのみ送信

        Args:
            tournament_id: 大会ID
            message: 送信するメッセージ
        """
        if tournament_id not in self.tournament_connections:
            # 大会固有のチャンネルがない場合は全体にブロードキャスト
            await self.broadcast(message)
            return

        # タイムスタンプを追加
        if "payload" in message and isinstance(message["payload"], dict):
            message["payload"]["timestamp"] = datetime.utcnow().isoformat()

        connections = self.tournament_connections[tournament_id][:]
        tasks = [self._send_safe(conn, message) for conn in connections]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_match_update(self, match_id: int, tournament_id: int,
                                 action: str = "updated", details: Optional[Dict] = None):
        """
        試合更新通知を送信

        Args:
            match_id: 試合ID
            tournament_id: 大会ID
            action: アクション種別 (updated, created, deleted)
            details: 追加の詳細情報
        """
        message = {
            "type": WebSocketEventType.MATCH_UPDATE,
            "payload": {
                "match_id": match_id,
                "tournament_id": tournament_id,
                "action": action,
                **(details or {})
            }
        }
        await self.broadcast(message)

    async def send_standing_update(self, tournament_id: int, group_id: str,
                                    details: Optional[Dict] = None):
        """
        順位表更新通知を送信

        Args:
            tournament_id: 大会ID
            group_id: グループID
            details: 追加の詳細情報
        """
        message = {
            "type": WebSocketEventType.STANDING_UPDATE,
            "payload": {
                "tournament_id": tournament_id,
                "group_id": group_id,
                **(details or {})
            }
        }
        await self.broadcast(message)

    async def send_approval_update(self, match_id: int, tournament_id: int,
                                    status: str, details: Optional[Dict] = None):
        """
        承認状態更新通知を送信

        Args:
            match_id: 試合ID
            tournament_id: 大会ID
            status: 承認状態 (pending, approved, rejected)
            details: 追加の詳細情報
        """
        message = {
            "type": WebSocketEventType.APPROVAL_UPDATE,
            "payload": {
                "match_id": match_id,
                "tournament_id": tournament_id,
                "approval_status": status,
                **(details or {})
            }
        }
        await self.broadcast(message)


# グローバルなインスタンスを作成
manager = ConnectionManager()
