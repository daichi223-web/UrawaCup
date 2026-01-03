@echo off
chcp 65001 >nul
echo.
echo ========================================
echo 浦和カップ 自動構築エージェント
echo ========================================
echo.

REM 仮想環境があれば有効化
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Pythonでインタラクティブモード実行
python run.py %*

pause
