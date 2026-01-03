@echo off
chcp 65001 > nul
echo ==========================================
echo UrawaCup Phase MINI 要件チェック
echo ==========================================

cd /d %~dp0
python main.py --phase MINI

pause
