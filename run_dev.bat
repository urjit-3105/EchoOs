@echo off
title ECHO WorkforceOS Launcher
echo =============================================================================
echo   ECHO WorkforceOS - Starting Enterprise Autonomous Platform
echo =============================================================================
echo.

cd /d "%~dp0"

echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "ECHO Backend API" cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --port 8000"

echo [2/2] Launching Next.js Frontend on http://localhost:3000 ...
start "ECHO Frontend Dashboard" cmd /k "cd frontend && npm run dev"

echo.
echo =============================================================================
echo   ECHO Services Launched!
echo   - Web Dashboard : http://localhost:3000/dashboard
echo   - Backend Docs  : http://127.0.0.1:8000/docs
echo   - Demo Admin    : admin@echo-workforceos.com / EchoDemo123!
echo =============================================================================
pause
