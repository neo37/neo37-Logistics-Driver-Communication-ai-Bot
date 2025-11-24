#!/bin/bash

# Script to start development environment locally (without Docker)

set -e

echo "========================================="
echo "Starting Driver Bot V2 (Development)"
echo "========================================="

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
echo "Installing dependencies..."
./venv/bin/pip install -q -r requirements.txt

# Initialize database
echo "Initializing database..."
mkdir -p data

# Start services in separate terminals/processes
echo ""
echo "Starting services..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $TELEGRAM_PID $VOICE_PID 2>/dev/null || true
    exit 0
}

trap cleanup EXIT INT TERM

# Start Telegram bo t in background
echo "Starting Telegram bot..."
DATABASE_URL="sqlite+aiosqlite:///./data/vehicles.db" ./venv/bin/python bot.py &
TELEGRAM_PID=$!

# Start Voice API in background
echo "Starting Voice API on http://localhost:8037..."
DATABASE_URL="sqlite+aiosqlite:///./data/vehicles.db" VOICE_API_PORT=8037 ./venv/bin/python voice_api.py &
VOICE_PID=$!

echo ""
echo "========================================="
echo "✅ Services started!"
echo "========================================="
echo "  - Telegram Bot (PID: $TELEGRAM_PID)"
echo "  - Voice API (PID: $VOICE_PID)"
echo "  - Voice Interface: http://localhost:8037"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
