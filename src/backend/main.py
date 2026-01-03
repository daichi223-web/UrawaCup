"""
浦和カップ トーナメント管理システム - バックエンドAPI
FastAPI + SQLAlchemy
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    print("浦和カップ API サーバー起動中...")
    init_db()
    print("データベース初期化完了")
    yield
    # 終了時の処理
    print("浦和カップ API サーバー終了")


# FastAPIアプリケーション作成
app = FastAPI(
    title="浦和カップ トーナメント管理システム API",
    description="さいたま市招待高校サッカーフェスティバル浦和カップの運営管理API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite開発サーバー
        "http://localhost:5174",  # Vite開発サーバー（代替ポート）
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターを登録
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "浦和カップ トーナメント管理システム API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}


# WebSocket setup
from fastapi import WebSocket, WebSocketDisconnect
from utils.websocket import manager

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # クライアントからのメッセージは現在は無視する（受信のみ）
            # keepaliveのために受信待ちを行う
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
