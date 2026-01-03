"""
浦和カップ トーナメント管理システム - ヘルスチェックテスト
"""

import pytest


class TestHealthCheck:
    """ヘルスチェックエンドポイントのテスト"""

    def test_health_check(self, client):
        """ヘルスチェックが正常に動作すること"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_endpoint(self, client):
        """ルートエンドポイントが正常に動作すること"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
