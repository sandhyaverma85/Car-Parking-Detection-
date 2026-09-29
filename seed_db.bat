@echo off
echo ========================================================
echo   Smart Curb Platform - Seeding Database
echo ========================================================
cd /d "%~dp0"
backend\.venv\Scripts\python.exe scripts\seed_db.py
pause
