@echo off
echo ========================================================
echo   Smart Curb Platform - Starting All Services
echo ========================================================
cd /d "%~dp0"

echo [1/3] Launching FastAPI Backend (Port 8000)...
start "Smart Curb - Backend" cmd /k "run_backend.bat"

timeout /t 3 /nobreak >nul

echo [2/3] Launching React Frontend (Port 5173)...
start "Smart Curb - Frontend" cmd /k "run_frontend.bat"

timeout /t 3 /nobreak >nul

echo [3/3] Launching AI Processing Pipeline...
start "Smart Curb - AI Pipeline" cmd /k "run_ai.bat"

echo.
echo All services launched!
echo - API Docs: http://localhost:8000/docs
echo - Web Dashboard: http://localhost:5173
echo.
pause
