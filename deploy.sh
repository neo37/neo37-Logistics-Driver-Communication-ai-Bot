#!/bin/bash

# Deployment script for Driver Communicator Bot V2
# This script deploys the updated bot with voice interface support
# Uses docker-compose for easy multi-service orchestration

set -e

PROJECT_NAME="driver_communicator_bot_v2"
COMPOSE_PROJECT_NAME="$PROJECT_NAME"

echo "========================================="
echo "Driver Communicator Bot V2 Deployment"
echo "========================================="

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with required environment variables"
    echo "See .env.example for reference"
    exit 1
fi

# Проверка наличия BOT_TOKEN
if ! grep -q "BOT_TOKEN=" .env || grep -q "BOT_TOKEN=$" .env; then
    echo "❌ Error: BOT_TOKEN not set in .env file!"
    exit 1
fi

echo "✅ Environment file found and validated"

# Остановка старого деплоя V2 (если существует)
echo ""
echo "Stopping previous V2 deployment (if exists)..."
docker-compose -p "$COMPOSE_PROJECT_NAME" down 2>/dev/null || true

# Сборка Docker образов
echo ""
echo "Building Docker images..."
docker-compose -p "$COMPOSE_PROJECT_NAME" build

# Запуск сервисов
echo ""
echo "Starting services..."
docker-compose -p "$COMPOSE_PROJECT_NAME" up -d

# Проверка статуса
echo ""
echo "Checking service status..."
sleep 3
docker-compose -p "$COMPOSE_PROJECT_NAME" ps

echo ""
echo "========================================="
echo "✅ Deployment complete!"
echo "========================================="
echo ""
echo "Services:"
echo "  - Telegram Bot: driver_bot_telegram"
echo "  - Voice API: driver_bot_voice (http://localhost:8037)"
echo "  - REST API: driver_bot_api (http://localhost:8036)"
echo ""
echo "View logs:"
echo "  docker-compose -p $COMPOSE_PROJECT_NAME logs -f"
echo ""
echo "Stop all services:"
echo "  docker-compose -p $COMPOSE_PROJECT_NAME down"
echo ""
