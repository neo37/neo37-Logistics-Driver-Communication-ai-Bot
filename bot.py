"""Объединённый Telegram бот с улучшенным LLM-советником для деликатных ответов"""
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from config import BOT_TOKEN
from database import Vehicle, VehicleStatus, VehicleType, CrewType, async_session_maker, init_db
from dialog_states import VehicleRegistration
from llm_service import handle_user_question

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def get_main_keyboard():
    """Клавиатура для главного меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
            [KeyboardButton(text="Помощь"), KeyboardButton(text="Связаться с менеджером")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )


def get_crew_keyboard():
    """Клавиатура для выбора типа экипажа"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Одиночный"), KeyboardButton(text="Парный")]
        ],
        resize_keyboard=True
    )


def get_vehicle_type_keyboard():
    """Клавиатура для выбора типа ТС"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Рефрижератор"), KeyboardButton(text="Тентованный")],
            [KeyboardButton(text="Открытый"), KeyboardButton(text="Контейнер")],
            [KeyboardButton(text="Цистерна"), KeyboardButton(text="Другое")]
        ],
        resize_keyboard=True
    )


def get_yes_no_keyboard():
    """Клавиатура Да/Нет"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")]
        ],
        resize_keyboard=True
    )


def get_destination_regions_keyboard():
    """Клавиатура для выбора региона назначения"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Москва"), KeyboardButton(text="Санкт-Петербург")],
            [KeyboardButton(text="Казань"), KeyboardButton(text="Екатеринбург")],
            [KeyboardButton(text="Новосибирск"), KeyboardButton(text="Краснодар")],
            [KeyboardButton(text="Ростов-на-Дону"), KeyboardButton(text="Нижний Новгород")],
            [KeyboardButton(text="Самара"), KeyboardButton(text="Уфа")],
            [KeyboardButton(text="Челябинск"), KeyboardButton(text="Воронеж")],
            [KeyboardButton(text="Другое")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите регион назначения"
    )


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    # Создаем новую запись о машине
    async with async_session_maker() as session:
        vehicle = Vehicle(
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            is_ready=True
        )
        session.add(vehicle)
        await session.commit()
        await session.refresh(vehicle)
        await state.update_data(vehicle_id=vehicle.id)
    
    # Более дружелюбное приветствие
    greeting = (
        "👋 Здравствуйте! Рад вас видеть!\n\n"
        "Я помогу вам зарегистрировать свободную машину в нашей системе. "
        "Это займёт всего несколько минут.\n\n"
        "Начнём с контактных данных. Укажите, пожалуйста, ваш контактный телефон:"
    )
    
    await message.answer(
        greeting,
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(VehicleRegistration.waiting_for_phone)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
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
    await message.answer(help_text)


@dp.message(F.text == "Помощь")
async def help_button(message: Message):
    """Обработчик кнопки Помощь"""
    await cmd_help(message)


@dp.message(F.text == "Связаться с менеджером")
async def contact_manager(message: Message):
    """Обработчик кнопки связи с менеджером"""
    await message.answer(
        "📞 Для связи с менеджером позвоните по телефону: +7 (XXX) XXX-XX-XX\n"
        "Или напишите на email: manager@example.com\n\n"
        "После связи с менеджером вы можете продолжить регистрацию, используя команду /start"
    )


@dp.message(StateFilter(VehicleRegistration.waiting_for_phone))
async def process_phone(message: Message, state: FSMContext):
    """Обработка контактных данных (ШАГ 1)"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    
    phone = message.text.strip()
    
    async with async_session_maker() as session:
        vehicle = await session.get(Vehicle, vehicle_id)
        if vehicle:
            vehicle.driver_phone = phone
            await session.commit()
    
    await message.answer(
        "Отлично! Теперь укажите, пожалуйста, ФИО водителя:"
    )
    await state.set_state(VehicleRegistration.waiting_for_driver_name)


@dp.message(StateFilter(VehicleRegistration.waiting_for_driver_name))
async def process_driver_name(message: Message, state: FSMContext):
    """Обработка ФИО водителя (ШАГ 2)"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    
    async with async_session_maker() as session:
        vehicle = await session.get(Vehicle, vehicle_id)
        if vehicle:
            vehicle.driver_name = message.text.strip()
            await session.commit()
    
    await message.answer(
        "Хорошо! Когда машина будет готова к отправке?\n\n"
        "Можете указать дату и время, например: 15.01.2024 10:00"
    )
    await state.set_state(VehicleRegistration.waiting_for_date)


@dp.message(StateFilter(VehicleRegistration.waiting_for_date))
async def process_date(message: Message, state: FSMContext):
    """Обработка даты готовности (ШАГ 3)"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    
    try:
        # Пытаемся распарсить дату (упрощенная версия)
        date_str = message.text.strip()
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                # Здесь можно добавить более сложный парсинг даты
                vehicle.ready_date = datetime.utcnow()  # Упрощенно, в реальности нужно парсить
                await session.commit()
        
        await message.answer(
            "Отлично! А какой тип транспортного средства?",
            reply_markup=get_vehicle_type_keyboard()
        )
        await state.set_state(VehicleRegistration.waiting_for_vehicle_type)
    except Exception as e:
        logger.error(f"Error processing date: {e}")
        await message.answer(
            "Кажется, формат даты не совсем правильный. "
            "Попробуйте указать в формате: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 15.01.2024 10:00"
        )




@dp.message(StateFilter(VehicleRegistration.waiting_for_vehicle_type))
async def process_vehicle_type(message: Message, state: FSMContext):
    """Обработка типа ТС (ШАГ 4)"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    
    vehicle_type_map = {
        "рефрижератор": VehicleType.REFRIGERATOR,
        "тентованн": VehicleType.TENT,
        "открыт": VehicleType.OPEN,
        "контейнер": VehicleType.CONTAINER,
        "цистерн": VehicleType.TANK,
    }
    
    vehicle_type = None
    text_lower = message.text.lower()
    for key, value in vehicle_type_map.items():
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
    
    await message.answer(
        "Хорошо! Теперь подскажите, пожалуйста, грузоподъемность или объем в кубических метрах.\n"
        "Например: 20",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(VehicleRegistration.waiting_for_capacity)


@dp.message(StateFilter(VehicleRegistration.waiting_for_capacity))
async def process_capacity(message: Message, state: FSMContext):
    """Обработка грузоподъемности/объема (ШАГ 5)"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    
    try:
        capacity = int(message.text.strip())
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                vehicle.capacity_cubic_meters = capacity
                await session.commit()
        
        await message.answer(
            "Отлично! А где сейчас находится ваша машина? "
            "Укажите город или регион:"
        )
        await state.set_state(VehicleRegistration.waiting_for_location)
    except ValueError:
        await message.answer(
            "Кажется, это не число. Попробуйте указать цифрами, например: 20"
        )


@dp.message(StateFilter(VehicleRegistration.waiting_for_location))
async def process_location(message: Message, state: FSMContext):
    """Обработка местоположения (ШАГ 6)"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    
    async with async_session_maker() as session:
        vehicle = await session.get(Vehicle, vehicle_id)
        if vehicle:
            vehicle.current_location = message.text.strip()
            await session.commit()
    
    await message.answer(
        "Понятно! А куда вы готовы поехать? Выберите регион назначения из списка или укажите свой вариант:",
        reply_markup=get_destination_regions_keyboard()
    )
    await state.set_state(VehicleRegistration.waiting_for_destination)


@dp.message(StateFilter(VehicleRegistration.waiting_for_destination))
async def process_destination(message: Message, state: FSMContext):
    """Обработка региона назначения (ШАГ 7)"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    
    destination = message.text.strip()
    
    # Если пользователь выбрал "Другое", просим указать регион вручную
    if destination.lower() in ["другое", "другой", "other"]:
        await message.answer(
            "Укажите, пожалуйста, регион назначения текстом:",
            reply_markup=ReplyKeyboardRemove()
        )
        return  # Остаемся в том же состоянии
    
    async with async_session_maker() as session:
        vehicle = await session.get(Vehicle, vehicle_id)
        if vehicle:
            vehicle.destination_region = destination
            await session.commit()
    
    # Определяем, какой пропуск спрашивать в зависимости от региона назначения
    destination_lower = destination.lower()
    if "казань" in destination_lower or "казан" in destination_lower:
        permit_city = "Казань"
        await state.update_data(permit_city="kazan")
    elif "москв" in destination_lower or "мск" in destination_lower:
        permit_city = "Москву"
        await state.update_data(permit_city="moscow")
    else:
        # Если регион не указан явно, спрашиваем про оба или делаем универсальный вопрос
        permit_city = "Казань или Москву"
        await state.update_data(permit_city="both")
    
    await message.answer(
        f"Хорошо! Есть ли у вас пропуск в {permit_city}?",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(VehicleRegistration.waiting_for_permit)


@dp.message(StateFilter(VehicleRegistration.waiting_for_permit))
async def process_permit(message: Message, state: FSMContext):
    """Обработка пропуска (ШАГ 8) - динамически для Казани или Москвы"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    permit_city = data.get("permit_city", "kazan")
    
    text_lower = message.text.lower()
    has_permit = text_lower in ["да", "yes", "есть", "есть пропуск"]
    
    async with async_session_maker() as session:
        vehicle = await session.get(Vehicle, vehicle_id)
        if vehicle:
            if permit_city == "kazan":
                vehicle.has_kazan_permit = has_permit
            elif permit_city == "moscow":
                vehicle.has_moscow_permit = has_permit
            elif permit_city == "both":
                # Если регион не был явно указан, сохраняем в оба поля
                vehicle.has_kazan_permit = has_permit
                vehicle.has_moscow_permit = has_permit
            await session.commit()
    
    await message.answer(
        "Отлично! И последний вопрос: какой тип экипажа у вас?",
        reply_markup=get_crew_keyboard()
    )
    await state.set_state(VehicleRegistration.waiting_for_crew)


@dp.message(StateFilter(VehicleRegistration.waiting_for_crew))
async def process_crew(message: Message, state: FSMContext):
    """Обработка типа экипажа (ШАГ 9 - финальный)"""
    data = await state.get_data()
    vehicle_id = data.get("vehicle_id")
    
    crew_type = None
    text_lower = message.text.lower()
    if "одиночн" in text_lower:
        crew_type = CrewType.SINGLE
    elif "парн" in text_lower:
        crew_type = CrewType.PAIR
    
    if crew_type:
        async with async_session_maker() as session:
            vehicle = await session.get(Vehicle, vehicle_id)
            if vehicle:
                vehicle.crew_type = crew_type
                vehicle.status = VehicleStatus.FREE  # Машина готова и свободна
                await session.commit()
        
        # Более дружелюбное завершение
        await message.answer(
            "✅ Отлично! Регистрация завершена!\n\n"
            "Спасибо, что заполнили все данные. Ваша машина добавлена в базу и будет рассмотрена "
            "для подбора подходящих маршрутов.\n\n"
            "Мы свяжемся с вами, когда найдем подходящий вариант.\n\n"
            "Если нужно зарегистрировать еще одну машину, просто напишите /start",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(VehicleRegistration.completed)
        await state.clear()
    else:
        await message.answer(
            "Давайте уточним: у вас одиночный или парный экипаж? "
            "Выберите один из вариантов."
        )




@dp.message()
async def handle_other_messages(message: Message, state: FSMContext):
    """Обработка всех остальных сообщений (вопросы, отклонения от сценария)"""
    current_state = await state.get_state()
    
    # Если пользователь не в процессе регистрации, предлагаем начать
    if current_state is None:
        # Используем LLM для более человечного ответа
        response = await handle_user_question(
            message.text,
            "Пользователь написал сообщение, но не начал регистрацию. "
            "Нужно дружелюбно предложить начать регистрацию командой /start",
            "начало диалога"
        )
        await message.answer(response)
        await message.answer(
            "Для начала регистрации машины используйте команду /start"
        )
        return
    
    # Если пользователь в процессе регистрации, но задает вопрос
    # Определяем текущий этап для контекста
    state_name = current_state.split(":")[-1] if current_state else None
    state_descriptions = {
        "waiting_for_phone": "ввод контактных данных",
        "waiting_for_driver_name": "ввод ФИО водителя",
        "waiting_for_date": "уточнение даты готовности",
        "waiting_for_vehicle_type": "определение типа транспортного средства",
        "waiting_for_capacity": "уточнение грузоподъемности и объема",
        "waiting_for_location": "определение текущего местоположения",
        "waiting_for_destination": "уточнение региона назначения",
        "waiting_for_permit": "проверка наличия пропуска",
        "waiting_for_crew": "выбор типа экипажа",
    }
    
    current_state_desc = state_descriptions.get(state_name, "регистрации машины")
    
    # Используем LLM для обработки вопроса с очеловечиванием
    response = await handle_user_question(
        message.text,
        f"Пользователь находится в процессе регистрации машины. "
        f"Текущий этап: {current_state_desc}. "
        f"Ответь на вопрос пользователя, но мягко напомни о необходимости продолжить заполнение данных.",
        current_state_desc
    )
    await message.answer(response)
    
    # Мягкие напоминания в зависимости от этапа
    reminders = {
        "waiting_for_phone": "Укажите, пожалуйста, ваш контактный телефон.",
        "waiting_for_driver_name": "Укажите, пожалуйста, ФИО водителя.",
        "waiting_for_date": "Когда машина будет готова? Укажите дату и время.",
        "waiting_for_vehicle_type": "Какой тип транспортного средства? Выберите из предложенных вариантов.",
        "waiting_for_capacity": "Укажите грузоподъемность или объем в кубических метрах.",
        "waiting_for_location": "Где сейчас находится ваша машина? Укажите город или регион.",
        "waiting_for_destination": "Куда вы готовы поехать? Выберите регион назначения из списка или укажите свой вариант.",
        "waiting_for_permit": "Есть ли у вас пропуск? (Да/Нет)",
        "waiting_for_crew": "Какой тип экипажа? Одиночный или парный?",
    }
    
    if state_name in reminders:
        await message.answer(reminders[state_name])


async def main():
    """Главная функция запуска бота"""
    # Инициализация БД
    await init_db()
    logger.info("Database initialized")
    
    # Запуск бота
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
