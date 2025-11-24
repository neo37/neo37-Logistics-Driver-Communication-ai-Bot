#!/bin/bash
set -e

# Загрузка переменных из .env файла, если он существует
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Параметры подключения (должны быть в .env или переданы как переменные окружения)
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_PASSWORD="${REMOTE_PASSWORD:-}"
REMOTE_DIR="${REMOTE_DIR:-/root/driver_communicator_bot}"

# Проверка наличия обязательных переменных
if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_PASSWORD" ]; then
    echo "Ошибка: Необходимо установить переменные окружения REMOTE_HOST и REMOTE_PASSWORD"
    echo "Создайте .env файл на основе .env.example и заполните необходимые значения"
    exit 1
fi

echo "=== Starting deployment of driver_communicator_bot ==="

# Проверка наличия sshpass
if ! command -v sshpass &> /dev/null; then
    echo "sshpass не установлен. Устанавливаю..."
    sudo apt-get update && sudo apt-get install -y sshpass
fi

# Создание временного каталога для архивации
TEMP_DIR=$(mktemp -d)
echo "Создание архива..."
tar -czf "$TEMP_DIR/driver_communicator_bot.tar.gz" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='venv' \
    --exclude='.git' \
    -C /home/n36/cpq/36 driver_communicator_bot

# Копирование файлов на удаленный сервер
echo "Копирование файлов на сервер..."
sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
    "$TEMP_DIR/driver_communicator_bot.tar.gz" \
    "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Выполнение команд на удаленном сервере
echo "Настройка на удаленном сервере..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
    set -e
    
    # Установка необходимых пакетов
    echo "Установка необходимых пакетов..."
    apt-get update -qq
    apt-get install -y -qq python3-venv python3-pip || true
    
    # Создание директории
    mkdir -p /root/driver_communicator_bot
    
    # Распаковка архива
    echo "Распаковка архива..."
    tar -xzf /tmp/driver_communicator_bot.tar.gz -C /root/
    rm /tmp/driver_communicator_bot.tar.gz
    
    # Переход в директорию проекта
    cd /root/driver_communicator_bot
    echo "Текущая директория: $(pwd)"
    echo "Содержимое директории:"
    ls -la
    
    # Удаление старого venv если есть проблемы
    if [ -d "venv" ]; then
        echo "Удаление старого venv..."
        rm -rf venv
    fi
    
    # Создание виртуального окружения
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    
    # Проверка создания venv
    if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
        echo "ОШИБКА: venv не создан правильно!"
        exit 1
    fi
    
    # Активация виртуального окружения и установка зависимостей
    echo "Активация venv и установка зависимостей..."
    source venv/bin/activate
    which python
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Проверка наличия .env файла
    if [ ! -f ".env" ]; then
        echo "Внимание: .env файл не найден. Бот будет использовать значения по умолчанию из config.py"
    fi
    
    # Создание systemd service файла
    echo "Создание systemd service..."
    cat > /etc/systemd/system/driver-communicator-bot.service << 'EOFSERVICE'
[Unit]
Description=Driver Communicator Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/driver_communicator_bot
Environment="PATH=/root/driver_communicator_bot/venv/bin"
ExecStart=/root/driver_communicator_bot/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOFSERVICE
    
    # Перезагрузка systemd и перезапуск сервиса
    echo "Перезагрузка systemd..."
    systemctl daemon-reload
    
    echo "Остановка старого сервиса (если запущен)..."
    systemctl stop driver-communicator-bot.service || true
    
    echo "Запуск сервиса..."
    systemctl enable driver-communicator-bot.service
    systemctl start driver-communicator-bot.service
    
    echo "Проверка статуса сервиса..."
    sleep 2
    systemctl status driver-communicator-bot.service --no-pager || true
    
    echo "=== Deployment completed on remote server ==="
ENDSSH

# Очистка временных файлов
rm -rf "$TEMP_DIR"

echo ""
echo "=== Deployment completed successfully ==="
echo "Проверить статус бота можно командой:"
echo "sshpass -p '$REMOTE_PASSWORD' ssh $REMOTE_USER@$REMOTE_HOST 'systemctl status driver-communicator-bot.service'"
echo ""
echo "Просмотр логов:"
echo "sshpass -p '$REMOTE_PASSWORD' ssh $REMOTE_USER@$REMOTE_HOST 'journalctl -u driver-communicator-bot.service -f'"

