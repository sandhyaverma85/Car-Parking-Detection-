@echo off
echo ========================================================
echo   Smart Curb Platform - Starting AI Ingestion Engine
echo   YOLO Vehicle Detection + ByteTrack + Violations
echo ========================================================
cd /d "%~dp0"
backend\.venv\Scripts\python.exe ai_engine\pipeline.py
pause
