"""Адаптер голосового интерфейса через Flask-SocketIO и Web Speech API"""
import logging
from typing import Dict, Any, Optional, List
from interfaces.base_interface import BaseInterface, InterfaceMessage

logger = logging.getLogger(__name__)


class VoiceAdapter(BaseInterface):
    """Адаптер для голосового интерфейса через веб-браузер"""
    
    def __init__(self, socketio):
        """
        Инициализация голосового адаптера
        
        Args:
            socketio: Экземпляр Flask-SocketIO для отправки сообщений
        """
        self.socketio = socketio
        # Хранилище сессий пользователей (в продакшене использовать Redis или БД)
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    async def send_message(self, user_id: str, message: InterfaceMessage) -> None:
        """
        Отправить текстовое сообщение пользователю (будет озвучено через Web Speech API)
        
        Args:
            user_id: Session ID пользователя
            message: Сообщение с текстом и опциями
        """
        # Отправляем сообщение через SocketIO
        self.socketio.emit('bot_message', {
            'text': message.text,
            'keyboard_options': message.keyboard_options,
            'remove_keyboard': message.remove_keyboard
        }, room=user_id)
        
        logger.info(f"Sent message to user {user_id}: {message.text[:50]}...")
    
    async def send_audio(self, user_id: str, text: str) -> None:
        """
        Отправить аудио ответ (использует TTS браузера)
        
        Args:
            user_id: Session ID пользователя
            text: Текст для озвучивания
        """
        # В случае браузерного интерфейса, TTS происходит на клиенте
        # Просто отправляем текст, клиент сам его озвучит
        await self.send_message(user_id, InterfaceMessage(text=text))
    
    async def get_user_session_data(self, user_id: str) -> Dict[str, Any]:
        """
        Получить данные сессии пользователя
        
        Args:
            user_id: Session ID пользователя
            
        Returns:
            Словарь с данными сессии
        """
        return self.sessions.get(user_id, {})
    
    async def update_user_session_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """
        Обновить данные сессии пользователя
        
        Args:
            user_id: Session ID пользователя
            data: Данные для обновления
        """
        if user_id not in self.sessions:
            self.sessions[user_id] = {}
        
        self.sessions[user_id].update(data)
        logger.info(f"Updated session data for user {user_id}")
    
    async def clear_user_session(self, user_id: str) -> None:
        """
        Очистить сессию пользователя
        
        Args:
            user_id: Session ID пользователя
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"Cleared session for user {user_id}")
    
    def sync_send_message(self, user_id: str, message: InterfaceMessage) -> None:
        """Синхронная версия send_message для использования в Flask routes"""
        self.socketio.emit('bot_message', {
            'text': message.text,
            'keyboard_options': message.keyboard_options,
            'remove_keyboard': message.remove_keyboard
        }, room=user_id)
