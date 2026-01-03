@echo off
chcp 65001 >nul
echo.
echo ========================================
echo 浦和カップ 自動構築エージェント - セットアップ
echo ========================================
echo.

REM Python仮想環境の作成
echo [1/3] 仮想環境を作成中...
python -m venv .venv
call .venv\Scripts\activate.bat

REM 依存関係のインストール
echo [2/3] 依存関係をインストール中...
pip install -r requirements.txt

REM Claude Code認証確認
echo [3/3] Claude Code認証確認...
echo.
echo Claude Agent SDK を使用するには、Claude Code での認証が必要です。
echo まだ認証していない場合は、以下のコマンドを実行してください:
echo.
echo   claude
echo.
echo または、環境変数 ANTHROPIC_API_KEY を設定してください。
echo.

echo ========================================
echo セットアップ完了！
echo.
echo 実行方法:
echo   start.bat          - インタラクティブモード
echo   start.bat --all    - 全タスク自動実行
echo ========================================
pause
