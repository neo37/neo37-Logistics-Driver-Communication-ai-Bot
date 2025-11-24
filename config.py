"""Конфигурация приложения"""
import os
from dotenv import load_dotenv

load_dotenv()

# Все секретные данные должны быть в .env файле
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://r-ai.business-pad.com/api/ai_request/")
LLM_API_AUTH = os.getenv("LLM_API_AUTH", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vehicles.db")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Настройки LLM
LLM_MODEL = "4o-mini"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2048

