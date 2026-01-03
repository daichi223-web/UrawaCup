#!/usr/bin/env python3
"""
agent-Check: UrawaCup操作テストエージェント
Claude Agent SDKを使用してユーザー操作をテストし、動作確認を行う
不明点や問題はISSUES.mdに記録する
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage
except ImportError:
    print("Error: claude-agent-sdk is not installed.")
    print("Install with: pip install claude-agent-sdk")
    sys.exit(1)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# プロジェクトルート
PROJECT_ROOT = Path("D:/UrawaCup")
ISSUES_FILE = PROJECT_ROOT / "ISSUES.md"

# テストシナリオ定義
TEST_SCENARIOS = [
    {
        "id": "T001",
        "name": "バックエンドAPI接続確認",
        "prompt": """
以下のコマンドでバックエンドAPIが正常に動作しているか確認してください：
1. curl http://localhost:8000/health または http://localhost:8000/docs にアクセス
2. レスポンスが正常か確認
3. 結果を報告（成功/失敗と詳細）
""",
        "tools": ["Bash"],
        "category": "infrastructure"
    },
    {
        "id": "T002",
        "name": "フロントエンド接続確認",
        "prompt": """
以下のコマンドでフロントエンドが正常に動作しているか確認してください：
1. curl http://localhost:5173 または http://localhost:5174 または http://localhost:5175 にアクセス
2. HTMLが返ってくるか確認
3. 結果を報告（成功/失敗と詳細）
""",
        "tools": ["Bash"],
        "category": "infrastructure"
    },
    {
        "id": "T003",
        "name": "会場一覧API確認",
        "prompt": """
会場一覧APIをテストしてください：
1. curl http://localhost:8000/venues?tournament_id=1 を実行
2. JSONレスポンスを確認
3. 会場データが含まれているか確認
4. for_final_day, is_finals_venue フィールドが存在するか確認
5. 結果を報告
""",
        "tools": ["Bash"],
        "category": "venue"
    },
    {
        "id": "T004",
        "name": "会場更新API確認（Boolean false送信）",
        "prompt": """
会場更新APIでboolean falseが正しく処理されるかテストしてください：
1. まず会場一覧を取得: curl http://localhost:8000/venues?tournament_id=1
2. 最初の会場のIDを確認
3. その会場を更新（for_final_day=falseを送信）:
   curl -X PATCH http://localhost:8000/venues/{id} -H "Content-Type: application/json" -d '{"for_final_day": false, "is_finals_venue": false}'
4. 更新後、再度会場を取得して値が変わったか確認
5. 結果を報告（for_final_day=falseが正しく保存されたか）

不明点や問題があれば詳しく報告してください。
""",
        "tools": ["Bash"],
        "category": "venue"
    },
    {
        "id": "T005",
        "name": "チーム一覧API確認",
        "prompt": """
チーム一覧APIをテストしてください：
1. curl http://localhost:8000/teams?tournamentId=1 を実行
2. JSONレスポンスを確認
3. teamsフィールドが配列として存在するか確認
4. 結果を報告
""",
        "tools": ["Bash"],
        "category": "team"
    },
    {
        "id": "T006",
        "name": "試合一覧API確認",
        "prompt": """
試合一覧APIをテストしてください：
1. curl http://localhost:8000/matches?tournament_id=1 を実行
2. JSONレスポンスを確認
3. matchesフィールドが存在するか確認
4. 結果を報告
""",
        "tools": ["Bash"],
        "category": "match"
    },
    {
        "id": "T007",
        "name": "フロントエンドビルド確認",
        "prompt": """
フロントエンドのTypeScriptエラーがないか確認してください：
1. cd D:/UrawaCup/src/frontend && npm run build 2>&1 | head -50 を実行
2. ビルドエラーがあるか確認
3. 結果を報告（成功/失敗とエラー内容）

エラーがある場合は詳細を報告してください。
""",
        "tools": ["Bash"],
        "category": "build"
    },
    {
        "id": "T008",
        "name": "重要ファイル存在確認",
        "prompt": """
重要なファイルが存在するか確認してください：
1. D:/UrawaCup/src/frontend/src/pages/Settings.tsx
2. D:/UrawaCup/src/frontend/src/pages/FinalDaySchedule.tsx
3. D:/UrawaCup/src/frontend/src/components/FinalsBracket.tsx
4. D:/UrawaCup/src/frontend/src/components/DraggableMatchList.tsx
5. D:/UrawaCup/src/backend/routes/venues.py
6. D:/UrawaCup/src/backend/schemas/venue.py

それぞれのファイルが存在するか確認し、結果を報告してください。
""",
        "tools": ["Glob", "Bash"],
        "category": "files"
    },
    {
        "id": "T009",
        "name": "createPortal実装確認",
        "prompt": """
ドラッグ&ドロップのcreatePortal実装を確認してください：
1. FinalsBracket.tsx で createPortal が import されているか確認
2. DraggableMatchList.tsx で createPortal が import されているか確認
3. FinalDaySchedule.tsx で createPortal が import されているか確認
4. 各ファイルでDragOverlayがcreatePortalで包まれているか確認
5. 結果を報告（各ファイルの実装状況）

grepコマンドを使用してください。
問題がある場合は詳細を報告してください。
""",
        "tools": ["Bash", "Grep"],
        "category": "dragdrop"
    },
    {
        "id": "T010",
        "name": "会場設定snake_case送信確認",
        "prompt": """
Settings.tsxで会場保存時にsnake_caseで送信しているか確認してください：
1. handleSaveVenue関数を確認
2. for_final_day, is_finals_venue がsnake_caseで送信されているか確認
3. 結果を報告

問題がある場合は詳細を報告してください。
""",
        "tools": ["Grep", "Read"],
        "category": "venue"
    },
    {
        "id": "T011",
        "name": "連打防止実装確認",
        "prompt": """
ドラッグ&ドロップの連打防止（重複API呼び出し防止）が実装されているか確認してください：
1. MatchSchedule.tsx で swappingRef が使われているか確認
2. FinalDaySchedule.tsx で swappingRef が使われているか確認
3. 結果を報告

問題がある場合は詳細を報告してください。
""",
        "tools": ["Grep", "Read"],
        "category": "dragdrop"
    },
    # ========== 新規追加: UI-API整合性テスト ==========
    {
        "id": "T012",
        "name": "フィルターUI→API連携確認",
        "prompt": """
フィルターUIの値が実際にAPIリクエストに使われているか確認してください：

1. MatchResult.tsx を読んで以下を確認：
   - フィルター用のuseState（dateFilter, venueFilter, statusFilter等）が定義されているか
   - fetchMatches関数内でこれらのフィルター値がAPIパラメータとして使われているか
   - フィルター変更時にfetchMatchesが呼ばれるか（useEffect確認）

2. MatchSchedule.tsx を読んで以下を確認：
   - フィルターUIとAPI呼び出しが連携しているか

3. 問題があれば報告（useState定義のみで実際には使われていない等）
""",
        "tools": ["Read", "Grep"],
        "category": "ui-api"
    },
    {
        "id": "T013",
        "name": "ハードコード値検出",
        "prompt": """
フロントエンドでハードコードされている値を検出してください：

1. 以下のパターンをgrepで検索：
   - 会場名のハードコード: "浦和南", "市立浦和", "浦和学院", "武南", "駒場"
   - 日付のハードコード: "day1", "day2", "day3", "Day1", "Day2", "Day3"
   - チーム名のハードコード

2. 検出したファイルを確認し、動的に取得すべき箇所か判定

3. 問題のある箇所を報告（ファイル名:行番号）

検索対象: D:/UrawaCup/src/frontend/src/
""",
        "tools": ["Grep", "Read"],
        "category": "ui-api"
    },
    {
        "id": "T014",
        "name": "API応答とUI表示の整合性",
        "prompt": """
APIレスポンスのフィールド名とフロントエンドの期待値が一致しているか確認：

1. 会場API (/api/venues/) のレスポンスを取得
2. src/frontend/src/features/venues/types.ts のVenue型定義を確認
3. フィールド名の不一致がないか確認（snake_case vs camelCase）

4. 試合API (/api/matches/) のレスポンスを取得
5. src/shared/types/index.ts のMatchWithDetails型定義を確認
6. フィールド名の不一致がないか確認

問題があれば詳細を報告
""",
        "tools": ["Bash", "Read"],
        "category": "ui-api"
    },
    # ========== 新規追加: データ整合性テスト ==========
    {
        "id": "T015",
        "name": "画面間データ整合性",
        "prompt": """
異なる画面で同じデータが一貫して表示されるか確認：

1. 試合一覧API (/api/matches/?tournament_id=1) で試合数を取得
2. 試合結果入力画面の表示数と一致するか確認
3. 試合日程画面の表示数と一致するか確認

4. チーム一覧API (/api/teams/?tournament_id=1) でチーム数を取得
5. 順位表画面のチーム数と一致するか確認

整合性に問題があれば報告
""",
        "tools": ["Bash"],
        "category": "data"
    },
    {
        "id": "T016",
        "name": "試合ステージ別表示確認",
        "prompt": """
試合のステージ（予選/準決勝/3決/決勝/研修）が正しく分類されているか確認：

1. /api/matches/?tournament_id=1 で全試合取得
2. stage別に試合数をカウント
3. 最終日の試合構成を確認:
   - semifinal: 2試合
   - third_place: 1試合
   - final: 1試合
   - training: 複数試合
4. 決勝トーナメント（semifinal, third_place, final）が駒場スタジアムで開催されているか確認

問題があれば報告
""",
        "tools": ["Bash"],
        "category": "data"
    },
    # ========== 新規追加: CRUD操作テスト ==========
    {
        "id": "T017",
        "name": "試合結果更新API確認",
        "prompt": """
試合結果更新APIが正しく動作するか確認：

1. 未完了の試合を1件取得
2. スコアを設定してPATCHリクエスト
3. 更新後のデータを再取得して確認
4. statusがcompletedになっているか確認

問題があれば報告
""",
        "tools": ["Bash"],
        "category": "crud"
    },
    {
        "id": "T018",
        "name": "チーム入れ替えAPI確認",
        "prompt": """
試合のチーム入れ替えAPIが正しく動作するか確認：

1. /api/matches/swap-teams エンドポイントの存在確認
2. APIドキュメント（/docs）でパラメータ確認
3. 結果を報告

問題があれば報告
""",
        "tools": ["Bash"],
        "category": "crud"
    },
    # ========== 新規追加: エラーハンドリングテスト ==========
    {
        "id": "T019",
        "name": "不正リクエストのエラーハンドリング",
        "prompt": """
APIが不正なリクエストに対して適切なエラーを返すか確認：

1. 存在しない会場ID: curl http://localhost:8000/api/venues/99999
2. 存在しない試合ID: curl http://localhost:8000/api/matches/99999
3. 不正なパラメータ: curl http://localhost:8000/api/venues/?tournament_id=invalid

適切な404/400エラーが返るか確認し報告
""",
        "tools": ["Bash"],
        "category": "error"
    },
    {
        "id": "T020",
        "name": "必須フィールドバリデーション",
        "prompt": """
必須フィールドが欠けた場合のバリデーションを確認：

1. 会場作成で名前なし:
   curl -X POST http://localhost:8000/api/venues/ -H "Content-Type: application/json" -d '{"tournament_id": 1}'

2. 適切なバリデーションエラーが返るか確認

問題があれば報告
""",
        "tools": ["Bash"],
        "category": "error"
    },
    # ========== 新規追加: 型安全性テスト ==========
    {
        "id": "T021",
        "name": "TypeScript型定義の完全性",
        "prompt": """
TypeScriptの型定義が完全か確認：

1. shared/types/index.ts を読む
2. 以下の型が定義されているか確認：
   - Venue (isFinalsVenue, forFinalDay含む)
   - Match, MatchWithDetails
   - Team
   - Goal
   - Tournament

3. 各型に必要なフィールドが揃っているか確認

問題があれば報告
""",
        "tools": ["Read"],
        "category": "types"
    },
    {
        "id": "T022",
        "name": "未使用インポート・変数検出",
        "prompt": """
未使用のインポートや変数がないか確認：

1. npm run build を実行
2. TS6133 (unused variable) や TS6196 (unused import) のエラーがないか確認
3. エラーがあれば詳細を報告

対象: D:/UrawaCup/src/frontend/
""",
        "tools": ["Bash"],
        "category": "types"
    },
    # ========== 新規追加: パフォーマンス・UXテスト ==========
    {
        "id": "T023",
        "name": "N+1クエリ問題確認",
        "prompt": """
API呼び出しでN+1問題がないか確認：

1. 試合一覧取得時に、各試合のチーム情報が含まれているか確認
   curl http://localhost:8000/api/matches/?tournament_id=1

2. レスポンスにhomeTeam, awayTeam, venue, goalsが展開されているか確認
3. 追加のAPIリクエストなしで必要な情報が取得できるか確認

問題があれば報告
""",
        "tools": ["Bash"],
        "category": "performance"
    },
    {
        "id": "T024",
        "name": "ローディング状態の実装確認",
        "prompt": """
各画面でローディング状態が適切に表示されるか確認：

1. 以下のファイルで isLoading / loading 状態が使われているか確認：
   - MatchResult.tsx
   - MatchSchedule.tsx
   - FinalDaySchedule.tsx
   - Settings.tsx

2. ローディング中の表示（スピナー等）が実装されているか確認

問題があれば報告
""",
        "tools": ["Grep", "Read"],
        "category": "ux"
    },
    # ========== 新規追加: セキュリティテスト ==========
    {
        "id": "T025",
        "name": "認証バイパス確認",
        "prompt": """
認証が必要なAPIに認証なしでアクセスできないか確認：

1. 管理者用APIに認証なしでアクセス試行
2. 適切に401/403が返るか確認

※現在の実装で認証が実装されているかも含めて報告
""",
        "tools": ["Bash"],
        "category": "security"
    },
    # ========== API・リクエスト系 ==========
    {
        "id": "T026",
        "name": "リクエストヘッダー確認",
        "prompt": """
APIリクエストに適切なヘッダーが設定されているか確認：

1. httpClient の設定を確認 (src/frontend/src/core/http.ts)
2. Content-Type: application/json が設定されているか
3. 認証ヘッダー（Authorization）の設定があるか

問題があれば報告
""",
        "tools": ["Read", "Grep"],
        "category": "api"
    },
    {
        "id": "T027",
        "name": "タイムアウト処理確認",
        "prompt": """
APIリクエストのタイムアウト処理が実装されているか確認：

1. axios/fetch の timeout 設定を確認
2. タイムアウト時のエラーハンドリングがあるか確認

grep -r "timeout" src/frontend/src/
""",
        "tools": ["Grep", "Read"],
        "category": "api"
    },
    {
        "id": "T028",
        "name": "重複リクエスト防止",
        "prompt": """
同一リクエストの連続送信を防止しているか確認：

1. ボタン連打時に複数リクエストが飛ばないか
2. disabled 属性やローディング状態での制御があるか
3. isPending, isLoading 等での制御を確認

対象: 保存ボタン、送信ボタン等
""",
        "tools": ["Grep", "Read"],
        "category": "api"
    },
    # ========== データ処理系 ==========
    {
        "id": "T029",
        "name": "Null/Undefined処理",
        "prompt": """
null/undefined の適切な処理を確認：

1. オプショナルチェイニング (?.) の使用を確認
2. デフォルト値 (?? や ||) の設定を確認
3. APIレスポンスの null チェックがあるか

grep -r "\\?\\." src/frontend/src/pages/ | head -20
grep -r "\\?\\?" src/frontend/src/pages/ | head -20
""",
        "tools": ["Grep"],
        "category": "data"
    },
    {
        "id": "T030",
        "name": "空配列ハンドリング",
        "prompt": """
データ0件時の表示が適切か確認：

1. matches.length === 0 の場合の表示を確認
2. teams.length === 0 の場合の表示を確認
3. 「データがありません」等のメッセージがあるか

grep -r "length === 0" src/frontend/src/
grep -r "データがありません" src/frontend/src/
""",
        "tools": ["Grep", "Read"],
        "category": "data"
    },
    {
        "id": "T031",
        "name": "日付フォーマット確認",
        "prompt": """
日付表示のフォーマットが統一されているか確認：

1. 日付表示のフォーマット関数を検索
2. toLocaleDateString, format 等の使用を確認
3. 一貫したフォーマット (YYYY-MM-DD 等) になっているか

grep -r "toLocaleDateString\\|formatDate\\|format(" src/frontend/src/
""",
        "tools": ["Grep", "Read"],
        "category": "data"
    },
    # ========== 状態管理系 ==========
    {
        "id": "T032",
        "name": "初期状態の妥当性",
        "prompt": """
useStateの初期値が適切か確認：

1. フォームの初期値が空文字や0で適切か
2. 配列の初期値が [] になっているか
3. オブジェクトの初期値が null か {} か確認

grep -r "useState\\(" src/frontend/src/pages/ | head -30
""",
        "tools": ["Grep", "Read"],
        "category": "state"
    },
    {
        "id": "T033",
        "name": "フォームリセット確認",
        "prompt": """
モーダルを閉じた時やキャンセル時にフォームがリセットされるか確認：

1. onClose 時に state をリセットしているか
2. 編集モーダルを閉じて再度開いた時に前の値が残らないか

対象: MatchEditModal.tsx, Settings.tsx 等
""",
        "tools": ["Read", "Grep"],
        "category": "state"
    },
    {
        "id": "T034",
        "name": "useEffectクリーンアップ",
        "prompt": """
useEffect のクリーンアップ関数が適切に実装されているか確認：

1. setInterval, setTimeout のクリアがあるか
2. イベントリスナーの解除があるか
3. AbortController でリクエストキャンセルしているか

grep -r "return () =>" src/frontend/src/
grep -r "clearInterval\\|clearTimeout" src/frontend/src/
""",
        "tools": ["Grep"],
        "category": "state"
    },
    # ========== UI/UX系 ==========
    {
        "id": "T035",
        "name": "空状態表示確認",
        "prompt": """
各一覧画面でデータが0件の時の表示を確認：

1. MatchResult.tsx - 試合がない場合
2. MatchSchedule.tsx - 試合がない場合
3. Settings.tsx - 会場がない場合

「〇〇がありません」のような案内があるか確認
""",
        "tools": ["Read", "Grep"],
        "category": "ux"
    },
    {
        "id": "T036",
        "name": "確認ダイアログ確認",
        "prompt": """
破壊的操作（削除等）の前に確認ダイアログがあるか確認：

1. 削除ボタンクリック時に confirm() があるか
2. 自動生成時に既存データ上書きの警告があるか

grep -r "confirm(" src/frontend/src/
grep -r "削除しますか\\|上書き" src/frontend/src/
""",
        "tools": ["Grep"],
        "category": "ux"
    },
    {
        "id": "T037",
        "name": "トースト通知確認",
        "prompt": """
操作後のフィードバック（成功/エラー通知）があるか確認：

1. toast.success, toast.error の使用を確認
2. 保存成功時の通知があるか
3. エラー時の通知があるか

grep -r "toast\\." src/frontend/src/
""",
        "tools": ["Grep"],
        "category": "ux"
    },
    # ========== エラー処理系（拡張） ==========
    {
        "id": "T038",
        "name": "500エラー処理確認",
        "prompt": """
サーバーエラー（500系）時の処理を確認：

1. try-catch でエラーをキャッチしているか
2. エラーメッセージをユーザーに表示しているか
3. エラー状態の管理（error state）があるか

grep -r "catch.*error\\|setError\\|error:" src/frontend/src/pages/
""",
        "tools": ["Grep", "Read"],
        "category": "error"
    },
    # ========== コード品質系（拡張） ==========
    {
        "id": "T039",
        "name": "any型使用検出",
        "prompt": """
TypeScriptでany型が使用されている箇所を検出：

1. 明示的な any の使用
2. 暗黙の any（型推論できない箇所）

grep -r ": any\\|as any" src/frontend/src/ --include="*.ts" --include="*.tsx"
""",
        "tools": ["Grep"],
        "category": "quality"
    },
    {
        "id": "T040",
        "name": "TODO/FIXME残存確認",
        "prompt": """
未対応のTODO/FIXMEコメントがないか確認：

grep -r "TODO\\|FIXME\\|XXX\\|HACK" src/frontend/src/ src/backend/
""",
        "tools": ["Grep"],
        "category": "quality"
    },
    {
        "id": "T041",
        "name": "マジックナンバー検出",
        "prompt": """
意味不明な数値リテラル（マジックナンバー）がないか確認：

1. タイムアウト値、リトライ回数等が定数化されているか
2. ステータスコード（200, 404等）が定数化されているか

問題のある箇所があれば報告
""",
        "tools": ["Grep", "Read"],
        "category": "quality"
    },
    # ========== パフォーマンス系（拡張） ==========
    {
        "id": "T042",
        "name": "useMemo/useCallback使用確認",
        "prompt": """
再レンダリング最適化が適切に行われているか確認：

1. 重い計算に useMemo が使われているか
2. コールバック関数に useCallback が使われているか
3. 特に一覧表示やフィルター処理

grep -r "useMemo\\|useCallback" src/frontend/src/pages/
""",
        "tools": ["Grep"],
        "category": "performance"
    },
    {
        "id": "T043",
        "name": "バンドルサイズ確認",
        "prompt": """
ビルド後のバンドルサイズを確認：

1. npm run build を実行
2. 各チャンクのサイズを確認
3. 500KB以上の大きなチャンクがないか確認

問題があれば報告
""",
        "tools": ["Bash"],
        "category": "performance"
    },
    # ========== セキュリティ系（拡張） ==========
    {
        "id": "T044",
        "name": "XSS脆弱性確認",
        "prompt": """
XSS脆弱性がないか確認：

1. dangerouslySetInnerHTML の使用箇所を確認
2. ユーザー入力をそのまま表示している箇所を確認

grep -r "dangerouslySetInnerHTML" src/frontend/src/
""",
        "tools": ["Grep"],
        "category": "security"
    },
    {
        "id": "T045",
        "name": "機密情報露出確認",
        "prompt": """
APIキーや機密情報がフロントエンドに露出していないか確認：

1. .env ファイルの内容を確認
2. ハードコードされた認証情報がないか

grep -r "API_KEY\\|SECRET\\|PASSWORD\\|apiKey\\|secret" src/frontend/
""",
        "tools": ["Grep", "Read"],
        "category": "security"
    },
    # ========== E2Eシナリオ系 ==========
    {
        "id": "T046",
        "name": "CRUD完全フロー確認",
        "prompt": """
会場のCRUD操作が一貫して動作するか確認：

1. 会場一覧取得
2. 会場作成 (POST)
3. 作成した会場の取得 (GET)
4. 会場更新 (PATCH)
5. 会場削除 (DELETE)

各操作が正常に動作するか確認
""",
        "tools": ["Bash"],
        "category": "e2e"
    },
    {
        "id": "T047",
        "name": "複数フィルター組合せ確認",
        "prompt": """
複数のフィルターを組み合わせた時に正常に動作するか確認：

1. 日付フィルター + 会場フィルター の組合せ
2. 日付フィルター + ステータスフィルター の組合せ
3. 全フィルター解除で全件表示されるか

API呼び出しで確認
""",
        "tools": ["Bash"],
        "category": "e2e"
    },
    # ========== アクセシビリティ系 ==========
    {
        "id": "T048",
        "name": "label紐付け確認",
        "prompt": """
フォーム要素に適切なlabelが紐付いているか確認：

1. <label htmlFor="..."> の使用を確認
2. input要素に id が設定されているか
3. aria-label の使用を確認

grep -r "htmlFor\\|aria-label" src/frontend/src/
""",
        "tools": ["Grep"],
        "category": "a11y"
    },
    {
        "id": "T049",
        "name": "フォーカス管理確認",
        "prompt": """
キーボード操作とフォーカス管理を確認：

1. モーダルオープン時にフォーカスが移動するか
2. Tab キーで要素を巡回できるか
3. autoFocus の使用を確認

grep -r "autoFocus\\|focus()" src/frontend/src/
""",
        "tools": ["Grep"],
        "category": "a11y"
    },
]


class TestResult:
    """テスト結果を格納するクラス"""
    def __init__(self, test_id: str, name: str, category: str):
        self.test_id = test_id
        self.name = name
        self.category = category
        self.status: Optional[str] = None  # "PASS", "FAIL", "ERROR"
        self.message: str = ""
        self.issues: list[str] = []  # 発見された問題
        self.duration: float = 0.0


class IssueTracker:
    """イシュー追跡クラス"""
    def __init__(self, issues_file: Path):
        self.issues_file = issues_file
        self.issues: list[dict] = []

    def add_issue(self, test_id: str, test_name: str, category: str,
                  issue_type: str, description: str, details: str = ""):
        """イシューを追加"""
        self.issues.append({
            "timestamp": datetime.now().isoformat(),
            "test_id": test_id,
            "test_name": test_name,
            "category": category,
            "type": issue_type,  # "BUG", "QUESTION", "IMPROVEMENT"
            "description": description,
            "details": details
        })

    def save(self):
        """イシューをファイルに保存"""
        if not self.issues:
            return

        # 既存の内容を読み込み
        existing_content = ""
        if self.issues_file.exists():
            existing_content = self.issues_file.read_text(encoding="utf-8")

        # 新しいイシューを追加
        new_section = f"\n\n## テスト実行: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for issue in self.issues:
            icon = {
                "BUG": "🐛",
                "QUESTION": "❓",
                "IMPROVEMENT": "💡",
                "ERROR": "❌"
            }.get(issue["type"], "📝")

            new_section += f"""### {icon} [{issue['test_id']}] {issue['description']}

- **カテゴリ**: {issue['category']}
- **テスト**: {issue['test_name']}
- **タイプ**: {issue['type']}
- **検出日時**: {issue['timestamp']}

{issue['details']}

---

"""

        # ファイルに書き込み
        if not existing_content:
            header = """# UrawaCup - Issues & Questions

このファイルはagent-Checkによって自動生成されます。
テスト実行中に発見された問題や不明点を記録します。

"""
            existing_content = header

        with open(self.issues_file, "w", encoding="utf-8") as f:
            f.write(existing_content + new_section)

        console.print(f"[yellow]イシューを記録しました: {self.issues_file}[/yellow]")


# グローバルイシュートラッカー
issue_tracker = IssueTracker(ISSUES_FILE)


async def run_single_test(scenario: dict, results: list[TestResult]) -> TestResult:
    """単一のテストシナリオを実行"""
    result = TestResult(
        test_id=scenario["id"],
        name=scenario["name"],
        category=scenario["category"]
    )

    start_time = datetime.now()
    full_response = []

    try:
        async for message in query(
            prompt=scenario["prompt"] + "\n\n不明点や問題があれば、必ず報告してください。",
            options=ClaudeAgentOptions(
                allowed_tools=scenario["tools"],
                max_turns=15,
            )
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        full_response.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.subtype == "success":
                    result.status = "PASS"
                else:
                    result.status = "FAIL"

        result.message = "\n".join(full_response)

        # レスポンスから成功/失敗を判定
        response_text = result.message.lower()

        # エラーキーワードの検出
        error_keywords = ["error", "failed", "失敗", "エラー", "問題", "不明", "見つかりません"]
        has_error = any(keyword in response_text for keyword in error_keywords)

        if has_error:
            result.status = "FAIL"
            # イシューを記録
            issue_tracker.add_issue(
                test_id=result.test_id,
                test_name=result.name,
                category=result.category,
                issue_type="BUG" if "error" in response_text or "エラー" in response_text else "QUESTION",
                description=f"{result.name}で問題を検出",
                details=result.message[-1000:] if len(result.message) > 1000 else result.message
            )
        elif result.status is None:
            result.status = "PASS"

        # 不明点キーワードの検出
        question_keywords = ["不明", "わからない", "確認が必要", "要調査"]
        if any(keyword in response_text for keyword in question_keywords):
            issue_tracker.add_issue(
                test_id=result.test_id,
                test_name=result.name,
                category=result.category,
                issue_type="QUESTION",
                description=f"{result.name}で不明点を検出",
                details=result.message[-1000:] if len(result.message) > 1000 else result.message
            )

    except Exception as e:
        result.status = "ERROR"
        result.message = str(e)
        issue_tracker.add_issue(
            test_id=result.test_id,
            test_name=result.name,
            category=result.category,
            issue_type="ERROR",
            description=f"{result.name}で実行エラー",
            details=str(e)
        )

    result.duration = (datetime.now() - start_time).total_seconds()
    results.append(result)
    return result


async def run_all_tests(categories: Optional[list[str]] = None) -> list[TestResult]:
    """全テストを実行"""
    results: list[TestResult] = []

    # カテゴリフィルタ
    scenarios = TEST_SCENARIOS
    if categories:
        scenarios = [s for s in scenarios if s["category"] in categories]

    console.print(Panel.fit(
        f"[bold blue]UrawaCup操作テスト開始[/bold blue]\n"
        f"テスト数: {len(scenarios)}\n"
        f"イシュー記録先: {ISSUES_FILE}",
        title="agent-Check"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for scenario in scenarios:
            task = progress.add_task(
                f"[cyan]{scenario['id']}[/cyan] {scenario['name']}...",
                total=1
            )

            result = await run_single_test(scenario, results)

            status_icon = {
                "PASS": "[green]✓[/green]",
                "FAIL": "[red]✗[/red]",
                "ERROR": "[yellow]![/yellow]"
            }.get(result.status, "?")

            progress.update(task, description=f"{status_icon} {scenario['name']}")
            progress.advance(task)

    # イシューを保存
    issue_tracker.save()

    return results


def print_results(results: list[TestResult]):
    """テスト結果を表示"""
    table = Table(title="テスト結果サマリー")
    table.add_column("ID", style="cyan")
    table.add_column("テスト名", style="white")
    table.add_column("カテゴリ", style="blue")
    table.add_column("結果", style="bold")
    table.add_column("時間(s)", style="dim")

    pass_count = 0
    fail_count = 0
    error_count = 0

    for result in results:
        status_style = {
            "PASS": "[green]PASS[/green]",
            "FAIL": "[red]FAIL[/red]",
            "ERROR": "[yellow]ERROR[/yellow]"
        }.get(result.status, result.status)

        if result.status == "PASS":
            pass_count += 1
        elif result.status == "FAIL":
            fail_count += 1
        else:
            error_count += 1

        table.add_row(
            result.test_id,
            result.name,
            result.category,
            status_style,
            f"{result.duration:.1f}"
        )

    console.print(table)

    # サマリー
    total = len(results)
    console.print(Panel(
        f"[green]PASS: {pass_count}[/green] | "
        f"[red]FAIL: {fail_count}[/red] | "
        f"[yellow]ERROR: {error_count}[/yellow] | "
        f"Total: {total}\n"
        f"Issues recorded: {len(issue_tracker.issues)}",
        title="結果サマリー"
    ))

    # 失敗したテストの詳細
    failed = [r for r in results if r.status != "PASS"]
    if failed:
        console.print("\n[bold red]失敗したテストの詳細:[/bold red]")
        for result in failed:
            console.print(f"\n[cyan]{result.test_id}[/cyan] {result.name}")
            msg = result.message[:500] + "..." if len(result.message) > 500 else result.message
            console.print(f"[dim]{msg}[/dim]")


def main():
    """メインエントリポイント"""
    import argparse

    parser = argparse.ArgumentParser(
        description="UrawaCup操作テストエージェント（不明点はISSUES.mdに記録）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
カテゴリ:
  infrastructure  - インフラ接続確認
  venue           - 会場関連
  team            - チーム関連
  match           - 試合関連
  build           - ビルド確認
  files           - ファイル存在確認
  dragdrop        - ドラッグ&ドロップ機能
  ui-api          - UI-API整合性
  data            - データ整合性
  crud            - CRUD操作
  error           - エラーハンドリング
  types           - 型安全性
  performance     - パフォーマンス
  ux              - UX/ローディング
  security        - セキュリティ
  api             - API・リクエスト
  state           - 状態管理
  quality         - コード品質
  e2e             - E2Eシナリオ
  a11y            - アクセシビリティ

使用例:
  python agent_check.py                    # 全テスト実行
  python agent_check.py -c venue           # 会場関連のみ
  python agent_check.py -c venue match     # 会場と試合関連
  python agent_check.py --list             # テスト一覧表示

不明点や問題は D:/UrawaCup/ISSUES.md に自動記録されます。
"""
    )
    parser.add_argument(
        "-c", "--category",
        nargs="+",
        help="テストするカテゴリを指定"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="テスト一覧を表示"
    )
    parser.add_argument(
        "--issues",
        action="store_true",
        help="現在のイシューを表示"
    )

    args = parser.parse_args()

    if args.list:
        table = Table(title="テストシナリオ一覧")
        table.add_column("ID", style="cyan")
        table.add_column("名前", style="white")
        table.add_column("カテゴリ", style="blue")
        table.add_column("ツール", style="dim")

        for scenario in TEST_SCENARIOS:
            table.add_row(
                scenario["id"],
                scenario["name"],
                scenario["category"],
                ", ".join(scenario["tools"])
            )

        console.print(table)
        return

    if args.issues:
        if ISSUES_FILE.exists():
            console.print(Panel(ISSUES_FILE.read_text(encoding="utf-8"), title="ISSUES.md"))
        else:
            console.print("[yellow]イシューファイルはまだありません[/yellow]")
        return

    # テスト実行
    try:
        results = asyncio.run(run_all_tests(args.category))
        print_results(results)

        # 失敗があれば終了コード1
        if any(r.status != "PASS" for r in results):
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]テスト中断[/yellow]")
        issue_tracker.save()  # 中断時もイシューを保存
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
