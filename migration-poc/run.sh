#!/bin/bash
# Quick start script for multi-agent extraction POC

echo "=========================================="
echo "Agentic C# Extraction POC - Quick Start"
echo "=========================================="
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python --version)"

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

# Install/upgrade requirements
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo ""
    echo "Please create .env with your OpenRouter API key:"
    echo "  1. cp .env.example .env"
    echo "  2. Edit .env and add OPENROUTER_API_KEY=sk_..."
    echo ""
    exit 1
fi

# Check API key is set
if ! grep -q "OPENROUTER_API_KEY=sk_" .env; then
    echo ""
    echo "❌ OPENROUTER_API_KEY not configured in .env"
    echo "Please update .env with your API key from https://openrouter.ai/keys"
    exit 1
fi

# Run orchestrator
echo ""
echo "🚀 Starting multi-agent orchestration..."
echo ""
python orchestrator.py

echo ""
echo "✨ Pipeline complete!"
echo "📁 Results saved to: output/"
