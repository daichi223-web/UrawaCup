@echo off
chcp 65001 > nul
echo ==========================================
echo UrawaCup 要件チェックSDK 実行
echo ==========================================

cd /d %~dp0

REM Pythonパス設定
set PYTHON_PATH=C:\Users\a713678\AppData\Local\Python\bin\python.exe
set PROJECT_ROOT=D:\UrawaCup

REM Pythonが存在するか確認
if not exist "%PYTHON_PATH%" (
    echo エラー: Pythonが見つかりません: %PYTHON_PATH%
    echo 環境に合わせてPYTHON_PATHを変更してください
    pause
    exit /b 1
)

REM フルチェック実行
"%PYTHON_PATH%" main.py --project "%PROJECT_ROOT%" --report --issues

echo.
echo ==========================================
echo チェック完了
echo ==========================================
pause
