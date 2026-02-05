#!/bin/bash
# Script to run the test suite for Gong MCP Server

set -e

echo "🔍 Checking Python version..."
python3 --version

echo ""
echo "📦 Installing test dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv..."
    uv sync --extra test
else
    echo "Using pip..."
    # Install test dependencies directly (avoiding editable mode issues with old pip)
    python3 -m pip install --user pytest pytest-asyncio pytest-cov pytest-mock pytest-httpx freezegun || {
        echo "⚠️  Failed to install with --user, trying without..."
        python3 -m pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-httpx freezegun
    }
    # Install project dependencies needed for tests
    python3 -m pip install --user httpx python-dotenv || {
        python3 -m pip install httpx python-dotenv
    }
fi

echo ""
echo "🧪 Running test suite with coverage..."
python3 -m pytest tests/ -v --cov=gong_mcp --cov-report=term-missing --cov-report=html

echo ""
echo "✅ Test suite complete!"
echo "📈 Coverage report: htmlcov/index.html"
