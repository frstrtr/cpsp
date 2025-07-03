#!/bin/bash

# TRON USDT Payment Monitor - Start Script

echo "🚀 Starting TRON USDT Payment Monitor..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your TronGrid API key before running again."
    exit 1
fi

echo "✅ Environment ready!"
echo "🌐 Starting Flask application on http://localhost:5000"
echo "🧪 Test interface available at: file://$(pwd)/test_interface.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python app.py
