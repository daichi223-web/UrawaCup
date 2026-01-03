"""
浦和カップ トーナメント管理システム - 設定

環境変数から設定を読み込み、アプリケーション全体で使用
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # アプリケーション基本設定
    app_name: str = "浦和カップ トーナメント管理システム"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # データベース設定
    database_url: str = "sqlite:///./urawa_cup.db"
    sql_echo: bool = False
    
    # 認証設定
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24時間
    
    # CORS設定
    cors_origins: str = "*"  # カンマ区切りで複数指定可能
    
    # ファイルアップロード設定
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "./uploads"
    
    # 報告書出力設定
    report_output_dir: str = "./reports"
    
    # 大会デフォルト設定
    default_match_duration: int = 50
    default_half_duration: int = 25
    default_interval_minutes: int = 15
    default_matches_per_day: int = 6
    
    # ログ設定
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> list[str]:
        """CORS許可オリジンをリストで取得"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()


def check_security_settings():
    """セキュリティ設定のチェックと警告"""
    import warnings
    s = get_settings()

    if s.secret_key == "your-secret-key-change-in-production":
        warnings.warn(
            "\n"
            "=" * 60 + "\n"
            "⚠️  警告: SECRET_KEY がデフォルト値のままです！\n"
            "本番環境では必ず .env ファイルで SECRET_KEY を設定してください。\n"
            "\n"
            "ランダムなキーを生成するコマンド:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            "=" * 60,
            UserWarning,
            stacklevel=2
        )


# 便利なエイリアス
settings = get_settings()

# 起動時にセキュリティチェックを実行
check_security_settings()
