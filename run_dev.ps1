# =============================================================================
# ECHO WorkforceOS - 1-Click Startup Script (PowerShell)
# Launches both FastAPI Backend and Next.js Frontend concurrently.
# =============================================================================

Write-Host "🚀 Starting ECHO WorkforceOS..." -ForegroundColor Cyan

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start Backend in new window
Write-Host "⚡ Launching FastAPI Backend (http://127.0.0.1:8000)..." -ForegroundColor Yellow
$BackendCmd = "cd '$Root\backend'; .\venv\Scripts\Activate.ps1; python -m uvicorn main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd

# 2. Start Frontend in new window
Write-Host "🌐 Launching Next.js Frontend (http://localhost:3000)..." -ForegroundColor Green
$FrontendCmd = "cd '$Root\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCmd

Write-Host "`n✅ Both services dispatched!" -ForegroundColor Cyan
Write-Host "• Dashboard: http://localhost:3000/dashboard" -ForegroundColor White
Write-Host "• API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "• Default Demo Admin: admin@echo-workforceos.com / EchoDemo123!`n" -ForegroundColor Gray
