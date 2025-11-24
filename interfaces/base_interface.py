"""Базовый интерфейс для всех транспортных адаптеров"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class InterfaceMessage:
    """Сообщение для отправки пользователю"""
    text: str
    keyboard_options: Optional[List[str]] = None
    remove_keyboard: bool = False


class BaseInterface(ABC):
    """Абстрактный базовый класс для всех интерфейсов (Telegram, Voice, Web и т.д.)"""
    
    @abstractmethod
    async def send_message(self, user_id: str, message: InterfaceMessage) -> None:
        """
        Отправить текстовое сообщение пользователю
        
        Args:
            user_id: Идентификатор пользователя в данном интерфейсе
            message: Сообщение с текстом и опциями клавиатуры
        """
        pass
    
    @abstractmethod
    async def send_audio(self, user_id: str, text: str) -> None:
        """
        Отправить аудио ответ пользователю (для голосового интерфейса)
        
        Args:
            user_id: Идентификатор пользователя
            text: Текст для преобразования в речь
        """
        pass
    
    @abstractmethod
    async def get_user_session_data(self, user_id: str) -> Dict[str, Any]:
        """
        Получить данные сессии пользователя
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            Словарь с данными сессии
        """
        pass
    
    @abstractmethod
    async def update_user_session_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """
        Обновить данные сессии пользователя
        
        Args:
            user_id: Идентификатор пользователя
            data: Данные для обновления
        """
        pass
    
    @abstractmethod
    async def clear_user_session(self, user_id: str) -> None:
        """
        Очистить сессию пользователя
        
        Args:
            user_id: Идентификатор пользователя
        """
        pass
