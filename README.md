# Driver Communicator Bot V2 🚛

Telegram бот и голосовой интерфейс для регистрации свободных транспортных средств с поддержкой голосового взаимодействия через Web Speech API.

## 🎯 Возможности

- ✅ **Telegram интерфейс** - классический бот с клавиатурой
- 🎤 **Голосовой интерфейс** - веб-приложение с распознаванием и синтезом речи
- 🧠 **LLM интеграция** - умные, деликатные ответы на вопросы пользователей
- 🗄️ **База данных** - SQLite для хранения информации о транспорте
- 📦 **Docker** - полная контейнеризация для легкого деплоя

## 🏗️ Архитектура

Проект использует **multi-interface архитектуру** с транспортно-независимым сервисным слоем:

```
├── service_layer.py          # Бизнес-логика (независима от интерфейса)
├── interfaces/
│   ├── base_interface.py     # Абстрактный базовый класс
│   ├── telegram_adapter.py   # Telegram интеграция (в bot.py)
│   └── voice_adapter.py      # Voice интеграция
├── bot.py                    # Telegram бот (aiogram)
├── voice_api.py              # Voice API (Flask + SocketIO)
├── api.py                    # REST API (FastAPI)
└── database.py               # Модели БД (SQLAlchemy)
```

### Процесс регистрации

1. Контактные данные (телефон)
2. ФИО водителя
3. Дата готовности
4. Тип транспортного средства
5. Грузоподъемность/объем
6. Текущее местоположение
7. Регион назначения
8. Наличие пропуска (Казань/Москва)
9. Тип экипажа (одиночный/парный)

## 🚀 Быстрый старт

### Требования

- Docker & Docker Compose ИЛИ
- Python 3.12+

### 1. Настройка окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните обязательные переменные:
```env
BOT_TOKEN=your_telegram_bot_token_here
LLM_API_URL=https://r-ai.business-pad.com/api/ai_request/
LLM_API_AUTH=your_llm_auth_token_here
```

### 2. Запуск с Docker (рекомендуется)

```bash
# Деплой всех сервисов
./deploy.sh
```

Сервисы будут доступны:
- **Telegram Bot** - автоматически подключится к Telegram
- **Voice Interface** - http://localhost:8037
- **REST API** - http://localhost:8036

### 3. Запуск локально (для разработки)

```bash
# Запуск в dev режиме
./run.sh
```

## 🎤 Голосовой интерфейс

Голосовой интерфейс использует **Web Speech API** (встроенный в Chrome/Edge):

- **Speech Recognition** - распознавание речи (STT) на стороне браузера
- **Speech Synthesis** - синтез речи (TTS) на стороне браузера
- **WebSocket** - real-time коммуникация через Flask-SocketIO

### Использование

1. Откройте http://localhost:8037 в Chrome или Edge
2. Разрешите доступ к микрофону
3. Нажмите кнопку микрофона и говорите
4. Бот ответит голосом и текстом

### Поддерживаемые браузеры

- ✅ Chrome/Chromium
- ✅ Edge
- ✅ Safari (частично)
- ❌ Firefox (Web Speech API недоступно)

## 🐳 Docker Compose

Проект использует 3 сервиса:

```yaml
services:
  telegram-bot    # Telegram бот
  voice-api       # Голосовой интерфейс (порт 8037)
  api-server      # REST API (порт 8036)
```

### Управление

```bash
# Просмотр логов
docker-compose -p driver_communicator_bot_v2 logs -f

# Перезапуск сервиса
docker-compose -p driver_communicator_bot_v2 restart voice-api

# Остановка всех сервисов
docker-compose -p driver_communicator_bot_v2 down
```

## 📁 Структура проекта

```
.
├── bot.py                    # Telegram бот
├── voice_api.py              # Voice API (Flask + SocketIO)
├── api.py                    # REST API (FastAPI)
├── service_layer.py          # Бизнес-логика
├── database.py               # Модели БД
├── llm_service.py            # LLM интеграция
├── dialog_states.py          # FSM состояния
├── config.py                 # Конфигурация
│
├── interfaces/               # Адаптеры интерфейсов
│   ├── base_interface.py
│   └── voice_adapter.py
│
├── templates/                # HTML шаблоны
│   └── voice_interface.html
│
├── static/                   # Статические файлы
│   ├── style.css
│   └── voice_interface.js
│
├── Dockerfile                # Docker образ
├── docker-compose.yml        # Оркестрация сервисов
├── deploy.sh                 # Скрипт деплоя
├── run.sh                    # Скрипт для разработки
└── requirements.txt          # Python зависимости
```

## 🔧 Конфигурация

### Переменные окружения

```env
# Telegram
BOT_TOKEN=                    # Токен Telegram бота

# LLM
LLM_API_URL=                  # URL LLM API
LLM_API_AUTH=                 # Токен авторизации LLM

# Database
DATABASE_URL=                 # SQLite URL (по умолчанию: sqlite+aiosqlite:///./vehicles.db)

# API Ports
API_PORT=8000                 # REST API порт (внутренний)
VOICE_API_PORT=8001           # Voice API порт (внутренний)

# Hosts
API_HOST=0.0.0.0
VOICE_API_HOST=0.0.0.0
```

### Порты (внешние)

- `8036` - REST API
- `8037` - Voice Interface

## 🛠️ Разработка

### Добавление нового интерфейса

1. Создайте класс-наследник `BaseInterface`:

```python
from interfaces.base_interface import BaseInterface

class MyAdapter(BaseInterface):
    async def send_message(self, user_id, message):
        # Ваша реализация
        pass
    
    # Реализуйте остальные методы...
```

2. Используйте `VehicleRegistrationService` для бизнес-логики:

```python
from service_layer import VehicleRegistrationService

service = VehicleRegistrationService()
response = await service.start_registration(user_id)
```

### Тестирование

```bash
# Запуск локально
./run.sh

# Проверка Telegram бота
# Отправьте /start боту в Telegram

# Проверка Voice Interface
# Откройте http://localhost:8037 в Chrome
```

## 📝 История изменений

### V2 (текущая версия)

- ✅ Исправлен баг с состоянием после завершения регистрации
- ✅ Добавлен транспортно-независимый сервисный слой
- ✅ Добавлен голосовой интерфейс с Web Speech API
- ✅ Docker Compose для multi-service деплоя
- ✅ Новая архитектура с адаптерами интерфейсов

### V1

- Telegram бот с FSM для регистрации
- LLM интеграция для ответов
- SQLite база данных

## 📄 Лицензия

Proprietary - Driver Communicator Project

## 👥 Контакты

Для вопросов и поддержки свяжитесь с командой разработки.
