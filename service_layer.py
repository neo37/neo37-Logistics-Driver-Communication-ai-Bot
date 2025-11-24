"""Транспортно-независимый сервисный слой для регистрации транспортных средств

Этот модуль содержит всю бизнес-логику регистрации, независимую от интерфейса
(Telegram, Voice, Web и т.д.)
"""
from enum import Enum
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime
from dataclasses import dataclass
import logging

from database import (
    Vehicle, VehicleStatus, VehicleType, CrewType,
    async_session_maker
)

logger = logging.getLogger(__name__)


class RegistrationStep(Enum):
    """Этапы регистрации транспортного средства"""
    PHONE = "phone"
    DRIVER_NAME = "driver_name"
    DATE = "date"
    VEHICLE_TYPE = "vehicle_type"
    CAPACITY = "capacity"
    LOCATION = "location"
    DESTINATION = "destination"
    PERMIT = "permit"
    CREW = "crew"
    COMPLETED = "completed"


@dataclass
class UserResponse:
    """Ответ пользователя на текущем этапе"""
    text: str
    user_id: int
    session_data: Dict[str, Any]


@dataclass
class BotResponse:
    """Ответ бота пользователю"""
    message: str
    keyboard_options: Optional[list] = None
    next_step: Optional[RegistrationStep] = None
    is_completed: bool = False
    error: Optional[str] = None


class VehicleRegistrationService:
    """Сервис регистрации транспортных средств"""
    
    # Карта для парсинга типов транспорта
    VEHICLE_TYPE_MAP = {
        "рефрижератор": VehicleType.REFRIGERATOR,
        "тентованн": VehicleType.TENT,
        "открыт": VehicleType.OPEN,
        "контейнер": VehicleType.CONTAINER,
        "цистерн": VehicleType.TANK,
    }
    
    # Часто встречающиеся регионы для клавиатуры
    COMMON_DESTINATIONS = [
        "Москва", "Санкт-Петербург", "Казань", "Екатеринбург",
        "Новосибирск", "Краснодар", "Ростов-на-Дону", "Нижний Новгород",
        "Самара", "Уфа", "Челябинск", "Воронеж", "Другое"
    ]
    
    async def start_registration(self, user_id: int, username: Optional[str] = None) -> BotResponse:
        """Начать новую регистрацию"""
        # Создаем новую запись о машине
        async with async_session_maker() as session:
            vehicle = Vehicle(
                telegram_user_id=user_id,
                telegram_username=username,
                is_ready=True
            )
            session.add(vehicle)
            await session.commit()
            await session.refresh(vehicle)
            vehicle_id = vehicle.id
        
        greeting = (
            "👋 Здравствуйте! Рад вас видеть!\n\n"
            "Я помогу вам зарегистрировать свободную машину в нашей системе. "
            "Это займёт всего несколько минут.\n\n"
            "Начнём с контактных данных. Укажите, пожалуйста, ваш контактный телефон:"
        )
        
        return BotResponse(
            message=greeting,
            next_step=RegistrationStep.PHONE,
            keyboard_options=None
        )
    
    async def process_step(self, user_response: UserResponse, current_step: RegistrationStep) -> BotResponse:
        """Обработать ответ пользователя на текущем этапе"""
        handlers = {
            RegistrationStep.PHONE: self._handle_phone,
            RegistrationStep.DRIVER_NAME: self._handle_driver_name,
            RegistrationStep.DATE: self._handle_date,
            RegistrationStep.VEHICLE_TYPE: self._handle_vehicle_type,
            RegistrationStep.CAPACITY: self._handle_capacity,
            RegistrationStep.LOCATION: self._handle_location,
            RegistrationStep.DESTINATION: self._handle_destination,
            RegistrationStep.PERMIT: self._handle_permit,
            RegistrationStep.CREW: self._handle_crew,
        }
        
        handler = handlers.get(current_step)
        if not handler:
            return BotResponse(
                message="Произошла ошибка в процессе регистрации.",
                error="Unknown step"
            )
        
        return await handler(user_response)
    
    async def _handle_phone(self, response: UserResponse) -> BotResponse:
        """Обработка контактных данных"""
        vehicle_id = response.session_data.get("vehicle_id")
        phone = response.text.strip()
        
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                vehicle.driver_phone = phone
                await session.commit()
        
        return BotResponse(
            message="Отлично! Теперь укажите, пожалуйста, ФИО водителя:",
            next_step=RegistrationStep.DRIVER_NAME
        )
    
    async def _handle_driver_name(self, response: UserResponse) -> BotResponse:
        """Обработка ФИО водителя"""
        vehicle_id = response.session_data.get("vehicle_id")
        
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                vehicle.driver_name = response.text.strip()
                await session.commit()
        
        return BotResponse(
            message=(
                "Хорошо! Когда машина будет готова к отправке?\n\n"
                "Можете указать дату и время, например: 15.01.2024 10:00"
            ),
            next_step=RegistrationStep.DATE
        )
    
    async def _handle_date(self, response: UserResponse) -> BotResponse:
        """Обработка даты готовности"""
        vehicle_id = response.session_data.get("vehicle_id")
        
        try:
            # Упрощенная версия - просто сохраняем текущую дату
            # В реальности нужен более сложный парсинг
            async with async_session_maker() as session:
                vehicle = await session.get(Vehicle, vehicle_id)
                if vehicle:
                    vehicle.ready_date = datetime.utcnow()
                    await session.commit()
            
            return BotResponse(
                message="Отлично! А какой тип транспортного средства?",
                next_step=RegistrationStep.VEHICLE_TYPE,
                keyboard_options=["Рефрижератор", "Тентованный", "Открытый", 
                                "Контейнер", "Цистерна", "Другое"]
            )
        except Exception as e:
            logger.error(f"Error processing date: {e}")
            return BotResponse(
                message=(
                    "Кажется, формат даты не совсем правильный. "
                    "Попробуйте указать в формате: ДД.ММ.ГГГГ ЧЧ:ММ\n"
                    "Например: 15.01.2024 10:00"
                ),
                next_step=RegistrationStep.DATE
            )
    
    async def _handle_vehicle_type(self, response: UserResponse) -> BotResponse:
        """Обработка типа ТС"""
        vehicle_id = response.session_data.get("vehicle_id")
        
        vehicle_type = None
        text_lower = response.text.lower()
        for key, value in self.VEHICLE_TYPE_MAP.items():
            if key in text_lower:
                vehicle_type = value
                break
        
        if not vehicle_type:
            vehicle_type = VehicleType.OTHER
        
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                vehicle.vehicle_type = vehicle_type
                await session.commit()
        
        return BotResponse(
            message=(
                "Хорошо! Теперь подскажите, пожалуйста, грузоподъемность или объем в кубических метрах.\n"
                "Например: 20"
            ),
            next_step=RegistrationStep.CAPACITY
        )
    
    async def _handle_capacity(self, response: UserResponse) -> BotResponse:
        """Обработка грузоподъемности/объема"""
        vehicle_id = response.session_data.get("vehicle_id")
        
        try:
            capacity = int(response.text.strip())
            async with async_session_maker() as session:
                vehicle = await session.get(Vehicle, vehicle_id)
                if vehicle:
                    vehicle.capacity_cubic_meters = capacity
                    await session.commit()
            
            return BotResponse(
                message=(
                    "Отлично! А где сейчас находится ваша машина? "
                    "Укажите город или регион:"
                ),
                next_step=RegistrationStep.LOCATION
            )
        except ValueError:
            return BotResponse(
                message="Кажется, это не число. Попробуйте указать цифрами, например: 20",
                next_step=RegistrationStep.CAPACITY
            )
    
    async def _handle_location(self, response: UserResponse) -> BotResponse:
        """Обработка местоположения"""
        vehicle_id = response.session_data.get("vehicle_id")
        
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                vehicle.current_location = response.text.strip()
                await session.commit()
        
        return BotResponse(
            message="Понятно! А куда вы готовы поехать? Выберите регион назначения из списка или укажите свой вариант:",
            next_step=RegistrationStep.DESTINATION,
            keyboard_options=self.COMMON_DESTINATIONS
        )
    
    async def _handle_destination(self, response: UserResponse) -> BotResponse:
        """Обработка региона назначения"""
        vehicle_id = response.session_data.get("vehicle_id")
        destination = response.text.strip()
        
        # Если пользователь выбрал "Другое", остаемся на том же этапе
        if destination.lower() in ["другое", "другой", "other"]:
            return BotResponse(
                message="Укажите, пожалуйста, регион назначения текстом:",
                next_step=RegistrationStep.DESTINATION
            )
        
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                vehicle.destination_region = destination
                await session.commit()
        
        # Определяем, какой пропуск спрашивать
        destination_lower = destination.lower()
        if "казань" in destination_lower or "казан" in destination_lower:
            permit_city = "Казань"
            permit_type = "kazan"
        elif "москв" in destination_lower or "мск" in destination_lower:
            permit_city = "Москву"
            permit_type = "moscow"
        else:
            permit_city = "Казань или Москву"
            permit_type = "both"
        
        # Сохраняем тип пропуска в сессии
        response.session_data["permit_city"] = permit_type
        
        return BotResponse(
            message=f"Хорошо! Есть ли у вас пропуск в {permit_city}?",
            next_step=RegistrationStep.PERMIT,
            keyboard_options=["Да", "Нет"]
        )
    
    async def _handle_permit(self, response: UserResponse) -> BotResponse:
        """Обработка пропуска"""
        vehicle_id = response.session_data.get("vehicle_id")
        permit_city = response.session_data.get("permit_city", "kazan")
        
        text_lower = response.text.lower()
        has_permit = text_lower in ["да", "yes", "есть", "есть пропуск"]
        
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                if permit_city == "kazan":
                    vehicle.has_kazan_permit = has_permit
                elif permit_city == "moscow":
                    vehicle.has_moscow_permit = has_permit
                elif permit_city == "both":
                    vehicle.has_kazan_permit = has_permit
                    vehicle.has_moscow_permit = has_permit
                await session.commit()
        
        return BotResponse(
            message="Отлично! И последний вопрос: какой тип экипажа у вас?",
            next_step=RegistrationStep.CREW,
            keyboard_options=["Одиночный", "Парный"]
        )
    
    async def _handle_crew(self, response: UserResponse) -> BotResponse:
        """Обработка типа экипажа (финальный этап)"""
        vehicle_id = response.session_data.get("vehicle_id")
        
        crew_type = None
        text_lower = response.text.lower()
        if "одиночн" in text_lower:
            crew_type = CrewType.SINGLE
        elif "парн" in text_lower:
            crew_type = CrewType.PAIR
        
        if crew_type:
            async with async_session_maker() as session:
                vehicle = await session.get(Vehicle, vehicle_id)
                if vehicle:
                    vehicle.crew_type = crew_type
                    vehicle.status = VehicleStatus.FREE
                    await session.commit()
            
            return BotResponse(
                message=(
                    "✅ Отлично! Регистрация завершена!\n\n"
                    "Спасибо, что заполнили все данные. Ваша машина добавлена в базу и будет рассмотрена "
                    "для подбора подходящих маршрутов.\n\n"
                    "Мы свяжемся с вами, когда найдем подходящий вариант.\n\n"
                    "Если нужно зарегистрировать еще одну машину, просто напишите /start"
                ),
                next_step=RegistrationStep.COMPLETED,
                is_completed=True
            )
        else:
            return BotResponse(
                message=(
                    "Давайте уточним: у вас одиночный или парный экипаж? "
                    "Выберите один из вариантов."
                ),
                next_step=RegistrationStep.CREW,
                keyboard_options=["Одиночный", "Парный"]
            )
    
    async def get_help_text(self) -> str:
        """Получить текст помощи"""
        return (
            "📋 Я помогу вам зарегистрировать свободную машину в системе.\n\n"
            "Процесс регистрации включает следующие шаги:\n"
            "1️⃣ Контактные данные\n"
            "2️⃣ ФИО водителя\n"
            "3️⃣ Дата готовности\n"
            "4️⃣ Тип транспортного средства\n"
            "5️⃣ Грузоподъемность/объем\n"
            "6️⃣ Текущее местоположение\n"
            "7️⃣ Регион назначения\n"
            "8️⃣ Наличие пропуска (в Казань или Москву, в зависимости от назначения)\n"
            "9️⃣ Тип экипажа (одиночный/парный)\n\n"
            "Если у вас возникнут вопросы, я постараюсь помочь. "
            "А если вопрос сложный, предложу связаться с менеджером.\n\n"
            "Для начала регистрации используйте команду /start"
        )
    
    async def get_contact_manager_text(self) -> str:
        """Получить контактные данные менеджера"""
        return (
            "📞 Для связи с менеджером позвоните по телефону: +7 (XXX) XXX-XX-XX\n"
            "Или напишите на email: manager@example.com\n\n"
            "После связи с менеджером вы можете продолжить регистрацию, используя команду /start"
        )
