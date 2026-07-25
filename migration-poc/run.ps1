# Quick start script for multi-agent extraction POC (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Agentic C# Extraction POC - Quick Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Python found: $(python --version)" -ForegroundColor Green

# Create venv if needed
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install/upgrade requirements
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Check for .env
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please create .env with your OpenRouter API key:"
    Write-Host "  1. Copy-Item .env.example .env"
    Write-Host "  2. Edit .env and add OPENROUTER_API_KEY=sk_..."
    Write-Host ""
    exit 1
}

# Check API key is set
$envContent = Get-Content .env -Raw
if (-not ($envContent -match "OPENROUTER_API_KEY=sk_")) {
    Write-Host ""
    Write-Host "❌ OPENROUTER_API_KEY not configured in .env" -ForegroundColor Red
    Write-Host "Please update .env with your API key from https://openrouter.ai/keys"
    exit 1
}

# Run orchestrator
Write-Host ""
Write-Host "🚀 Starting multi-agent orchestration..." -ForegroundColor Cyan
Write-Host ""
python orchestrator.py

Write-Host ""
Write-Host "✨ Pipeline complete!" -ForegroundColor Green
Write-Host "📁 Results saved to: output/" -ForegroundColor Green
