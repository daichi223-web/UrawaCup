#!/usr/bin/env python
"""
バックエンドサーバー起動スクリプト
sys.pathを設定して相対インポートを解決
"""

import sys
import os

# backendディレクトリをsys.pathに追加
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 環境変数の設定
os.environ.setdefault('PYTHONPATH', backend_dir)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[backend_dir],
    )
