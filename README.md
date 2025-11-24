# Logistics Driver Communication Bot

AI-powered Telegram bot for logistics companies to communicate with drivers and register available vehicles.

## Описание / Description

Telegram-бот с AI-ассистентом для логистических компаний. Помогает водителям регистрировать свободные машины в системе через удобный диалог. Бот использует LLM для обработки вопросов и естественного общения с водителями.

**Features:**
- 🤖 AI-powered conversation with LLM integration
- 🚛 Vehicle registration workflow
- 📊 SQLite database for vehicle management
- 🔄 State machine for multi-step registration
- 💬 Natural language processing for user questions
- 📱 Telegram Bot API integration

## Технологии / Technologies

- Python 3.12+
- aiogram (Telegram Bot Framework)
- SQLAlchemy (Async ORM)
- SQLite database
- LLM API integration
- FSM (Finite State Machine) for dialog management

## Установка / Installation

```bash
pip install -r requirements.txt
```

## Настройка / Configuration

Создайте файл `.env` с переменными окружения:

```env
BOT_TOKEN=your_telegram_bot_token
LLM_API_URL=https://your-llm-api-url
LLM_API_AUTH=Basic your_auth_token
DATABASE_URL=sqlite+aiosqlite:///./vehicles.db
```

## Запуск / Running

```bash
python bot.py
```

или

```bash
./run.sh
```

## API

REST API доступен на порту 8000 (по умолчанию). См. `api.py` для деталей.

## Лицензия / License

MIT

