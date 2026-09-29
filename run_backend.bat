@echo off
echo ========================================================
echo   Smart Curb Platform - Starting FastAPI Backend
echo   Swagger Docs: http://localhost:8000/docs
echo ========================================================
cd /d "%~dp0backend"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
