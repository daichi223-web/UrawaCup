"""
浦和カップ SDK生成エージェント - 要件解析
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    REQUIREMENT_SPEC_PATH,
    SYSTEM_DESIGN_PATH,
    ROOT_CAUSE_ANALYSIS_PATH,
    DATABASE_STRUCTURE_PATH,
    FEATURES,
)


@dataclass
class FeatureRequirement:
    """Feature要件定義"""
    name: str
    description: str
    api_endpoints: List[str]
    data_types: List[str]
    dependencies: List[str]
    priority: int


@dataclass
class ArchitectureRequirement:
    """アーキテクチャ要件"""
    http_client: Dict[str, Any]
    auth_manager: Dict[str, Any]
    error_handling: Dict[str, Any]
    naming_convention: Dict[str, Any]


class RequirementAnalyzer:
    """要件解析クラス"""

    def __init__(self):
        self.requirement_content = ""
        self.system_design_content = ""
        self.root_cause_content = ""
        self.database_content = ""
        self._load_documents()

    def _load_documents(self):
        """ドキュメントを読み込み"""
        if REQUIREMENT_SPEC_PATH.exists():
            self.requirement_content = REQUIREMENT_SPEC_PATH.read_text(encoding="utf-8")

        if SYSTEM_DESIGN_PATH.exists():
            self.system_design_content = SYSTEM_DESIGN_PATH.read_text(encoding="utf-8")

        if ROOT_CAUSE_ANALYSIS_PATH.exists():
            self.root_cause_content = ROOT_CAUSE_ANALYSIS_PATH.read_text(encoding="utf-8")

        if DATABASE_STRUCTURE_PATH.exists():
            self.database_content = DATABASE_STRUCTURE_PATH.read_text(encoding="utf-8")

    def get_feature_requirements(self) -> List[FeatureRequirement]:
        """Feature要件を解析"""
        features = []

        feature_configs = {
            "tournaments": {
                "description": "大会管理機能",
                "api_endpoints": ["/tournaments", "/tournaments/{id}"],
                "data_types": ["Tournament", "CreateTournamentInput", "UpdateTournamentInput"],
                "dependencies": [],
                "priority": 1,
            },
            "teams": {
                "description": "チーム管理機能",
                "api_endpoints": ["/teams", "/teams/{id}", "/teams/import"],
                "data_types": ["Team", "CreateTeamInput", "UpdateTeamInput"],
                "dependencies": ["tournaments"],
                "priority": 1,
            },
            "players": {
                "description": "選手管理機能",
                "api_endpoints": ["/players", "/players/{id}"],
                "data_types": ["Player", "CreatePlayerInput", "UpdatePlayerInput"],
                "dependencies": ["teams"],
                "priority": 2,
            },
            "matches": {
                "description": "試合管理・結果入力機能",
                "api_endpoints": [
                    "/matches",
                    "/matches/{id}",
                    "/matches/{id}/result",
                    "/matches/generate-schedule/{tournament_id}",
                ],
                "data_types": ["Match", "MatchResult", "Goal", "CreateMatchInput"],
                "dependencies": ["teams", "venues"],
                "priority": 1,
            },
            "standings": {
                "description": "順位表自動計算機能",
                "api_endpoints": ["/standings", "/standings/top-scorers"],
                "data_types": ["Standing", "TeamStanding", "TopScorer"],
                "dependencies": ["matches"],
                "priority": 1,
            },
            "exclusions": {
                "description": "対戦除外設定機能",
                "api_endpoints": ["/exclusions", "/exclusions/{id}"],
                "data_types": ["MatchExclusion", "CreateExclusionInput"],
                "dependencies": ["teams"],
                "priority": 2,
            },
            "reports": {
                "description": "報告書生成機能",
                "api_endpoints": ["/reports/generate", "/reports/download/{id}"],
                "data_types": ["ReportConfig", "ReportOutput"],
                "dependencies": ["matches", "standings"],
                "priority": 2,
            },
            "venues": {
                "description": "会場管理機能",
                "api_endpoints": ["/venues", "/venues/{id}"],
                "data_types": ["Venue", "CreateVenueInput", "UpdateVenueInput"],
                "dependencies": ["tournaments"],
                "priority": 2,
            },
        }

        for feature_name in FEATURES:
            if feature_name in feature_configs:
                config = feature_configs[feature_name]
                features.append(FeatureRequirement(
                    name=feature_name,
                    description=config["description"],
                    api_endpoints=config["api_endpoints"],
                    data_types=config["data_types"],
                    dependencies=config["dependencies"],
                    priority=config["priority"],
                ))

        return sorted(features, key=lambda x: x.priority)

    def get_architecture_requirements(self) -> ArchitectureRequirement:
        """アーキテクチャ要件を解析"""
        return ArchitectureRequirement(
            http_client={
                "singleton": True,
                "location": "src/core/http/client.ts",
                "base_url": "import.meta.env.VITE_API_BASE_URL || '/api'",
                "timeout": 10000,
                "interceptors": ["auth", "transform", "error"],
            },
            auth_manager={
                "singleton": True,
                "location": "src/core/auth/manager.ts",
                "token_storage": "memory",  # メモリ管理、localStorageから読み込み
                "methods": ["setToken", "getToken", "clearToken", "isAuthenticated"],
            },
            error_handling={
                "format": "AppError",
                "location": "src/core/errors/types.ts",
                "codes": [
                    "BAD_REQUEST",
                    "UNAUTHORIZED",
                    "FORBIDDEN",
                    "NOT_FOUND",
                    "CONFLICT",
                    "VERSION_CONFLICT",
                    "VALIDATION_ERROR",
                    "OFFLINE",
                    "SERVER_ERROR",
                    "UNKNOWN",
                ],
                "fastapi_support": True,  # { detail: "..." } 形式対応
            },
            naming_convention={
                "frontend": "camelCase",
                "backend": "snake_case",
                "auto_transform": True,
                "interceptor_location": "src/core/http/interceptors/transform.ts",
            },
        )

    def get_known_issues(self) -> List[Dict[str, Any]]:
        """RootCauseAnalysis.mdから既知の問題を抽出"""
        issues = []

        if not self.root_cause_content:
            return issues

        # 問題パターンを抽出
        patterns = [
            {
                "pattern": r"HTTPクライアント.*?重複|3つのHTTPクライアント",
                "issue": "HTTPクライアント重複",
                "severity": "critical",
                "fix": "src/core/http/client.tsに統一",
            },
            {
                "pattern": r"snake_case.*?camelCase|命名規則.*?不整合",
                "issue": "命名規則不整合",
                "severity": "high",
                "fix": "インターセプターで自動変換",
            },
            {
                "pattern": r"FastAPI.*?detail|エラーメッセージ.*?表示されない",
                "issue": "エラーメッセージ未対応",
                "severity": "high",
                "fix": "errorInterceptorでFastAPI形式を解析",
            },
            {
                "pattern": r"認証.*?分散|トークン.*?不整合",
                "issue": "認証管理分散",
                "severity": "high",
                "fix": "AuthManagerで一元管理",
            },
        ]

        for p in patterns:
            if re.search(p["pattern"], self.root_cause_content, re.IGNORECASE):
                issues.append({
                    "issue": p["issue"],
                    "severity": p["severity"],
                    "fix": p["fix"],
                })

        return issues

    def get_database_entities(self) -> List[str]:
        """データベースエンティティ一覧を取得"""
        entities = []

        if not self.database_content:
            return entities

        # テーブル名を抽出
        table_pattern = r"(?:##\s*\d+\.\s*|CREATE TABLE\s+)(\w+)"
        matches = re.findall(table_pattern, self.database_content)

        return list(set(matches))

    def generate_prompt_context(self) -> str:
        """プロンプト用コンテキストを生成"""
        arch_req = self.get_architecture_requirements()
        features = self.get_feature_requirements()
        issues = self.get_known_issues()

        context = """
# 浦和カップ SDK生成コンテキスト

## アーキテクチャ原則

### 1. HTTPクライアント
- シングルトン: {singleton}
- 配置場所: {http_location}
- タイムアウト: {timeout}ms
- インターセプター: {interceptors}

### 2. 認証管理
- シングルトン: {auth_singleton}
- 配置場所: {auth_location}
- メソッド: {auth_methods}

### 3. エラー処理
- 形式: {error_format}
- FastAPI対応: {fastapi_support}
- エラーコード: {error_codes}

### 4. 命名規則
- フロントエンド: {frontend_case}
- バックエンド: {backend_case}
- 自動変換: {auto_transform}

## 生成対象Feature
{features_list}

## 既知の問題（解決必須）
{issues_list}
""".format(
            singleton=arch_req.http_client["singleton"],
            http_location=arch_req.http_client["location"],
            timeout=arch_req.http_client["timeout"],
            interceptors=", ".join(arch_req.http_client["interceptors"]),
            auth_singleton=arch_req.auth_manager["singleton"],
            auth_location=arch_req.auth_manager["location"],
            auth_methods=", ".join(arch_req.auth_manager["methods"]),
            error_format=arch_req.error_handling["format"],
            fastapi_support=arch_req.error_handling["fastapi_support"],
            error_codes=", ".join(arch_req.error_handling["codes"]),
            frontend_case=arch_req.naming_convention["frontend"],
            backend_case=arch_req.naming_convention["backend"],
            auto_transform=arch_req.naming_convention["auto_transform"],
            features_list="\n".join([
                f"- {f.name}: {f.description} (優先度: {f.priority})"
                for f in features
            ]),
            issues_list="\n".join([
                f"- [{i['severity'].upper()}] {i['issue']}: {i['fix']}"
                for i in issues
            ]) if issues else "- なし",
        )

        return context


if __name__ == "__main__":
    analyzer = RequirementAnalyzer()

    print("=== Feature要件 ===")
    for feature in analyzer.get_feature_requirements():
        print(f"- {feature.name}: {feature.description}")

    print("\n=== アーキテクチャ要件 ===")
    arch = analyzer.get_architecture_requirements()
    print(f"HTTPクライアント: {arch.http_client['location']}")
    print(f"認証管理: {arch.auth_manager['location']}")

    print("\n=== 既知の問題 ===")
    for issue in analyzer.get_known_issues():
        print(f"- [{issue['severity']}] {issue['issue']}")

    print("\n=== プロンプトコンテキスト ===")
    print(analyzer.generate_prompt_context())
