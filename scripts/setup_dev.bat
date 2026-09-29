@echo off
REM =============================================================================
REM  setup_dev.bat — Local development environment setup (Windows)
REM  AI-Powered Smart Curb & Parking Intelligence Platform
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo =========================================================
echo  Smart Curb ^& Parking Platform — Dev Setup
echo =========================================================
echo.

REM ── 1. Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not on PATH.
    echo         Download from https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i

REM ── 2. Check Node.js ─────────────────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js is not installed. Required for the frontend (Phase 11).
    echo           Download from https://nodejs.org/
) else (
    for /f "tokens=*" %%i in ('node --version') do echo [OK] Node.js %%i
)

REM ── 3. Copy .env if missing ───────────────────────────────────────────────────
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [INFO] .env created from .env.example.
    echo        IMPORTANT: Edit .env and fill in real values before running.
) else (
    echo [OK] .env already exists.
)

REM ── 4. Backend virtual environment ───────────────────────────────────────────
if not exist "backend\.venv" (
    echo [INFO] Creating backend virtual environment...
    python -m venv backend\.venv
    echo [OK] Backend venv created.
) else (
    echo [OK] Backend venv exists.
)

echo [INFO] Installing backend dependencies...
call backend\.venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r backend\requirements.txt
call backend\.venv\Scripts\deactivate.bat
echo [OK] Backend dependencies installed.

REM ── 5. AI Engine virtual environment ─────────────────────────────────────────
if not exist "ai_engine\.venv" (
    echo [INFO] Creating AI engine virtual environment...
    python -m venv ai_engine\.venv
    echo [OK] AI engine venv created.
) else (
    echo [OK] AI engine venv exists.
)

echo [INFO] Installing AI engine dependencies...
call ai_engine\.venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r ai_engine\requirements.txt
call ai_engine\.venv\Scripts\deactivate.bat
echo [OK] AI engine dependencies installed.

echo.
echo =========================================================
echo  NOTE: PyTorch is NOT installed automatically.
echo  Choose the correct version for your hardware:
echo.
echo  CPU only:
echo    ai_engine\.venv\Scripts\pip install torch torchvision ^
echo      --index-url https://download.pytorch.org/whl/cpu
echo.
echo  CUDA 12.1 (NVIDIA GPU):
echo    ai_engine\.venv\Scripts\pip install torch torchvision ^
echo      --index-url https://download.pytorch.org/whl/cu121
echo =========================================================
echo.

REM ── 6. Ensure required dirs exist ────────────────────────────────────────────
if not exist "logs" mkdir logs
if not exist "evidence" mkdir evidence
if not exist "data\videos" mkdir data\videos
if not exist "data\configs" mkdir data\configs

echo [OK] Required directories are ready.
echo.
echo =========================================================
echo  Setup complete. Next steps:
echo   1. Edit .env with your database credentials and JWT secret.
echo   2. Start PostgreSQL (or use Docker: docker compose up db -d).
echo   3. Run the backend:
echo        cd backend
echo        .venv\Scripts\activate
echo        python -m app.main
echo   4. (Phase 2+) Run the AI engine:
echo        cd ai_engine
echo        .venv\Scripts\activate
echo        python main.py
echo =========================================================
echo.

endlocal
