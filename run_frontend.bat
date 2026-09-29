@echo off
echo ========================================================
echo   Smart Curb Platform - Starting React Dashboard
echo   Web App URL: http://localhost:5173
echo ========================================================
cd /d "%~dp0\frontend"
npm.cmd run dev
pause
