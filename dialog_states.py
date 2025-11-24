"""Состояния диалога FSM"""
from aiogram.fsm.state import State, StatesGroup


class VehicleRegistration(StatesGroup):
    """Состояния регистрации машины"""
    # Новый порядок регистрации:
    waiting_for_phone = State()  # 1. Ожидание контактных данных
    waiting_for_driver_name = State()  # 2. Ожидание ФИО водителя
    waiting_for_date = State()  # 3. Ожидание даты готовности
    waiting_for_vehicle_type = State()  # 4. Ожидание типа ТС
    waiting_for_capacity = State()  # 5. Ожидание грузоподъемности/объема
    waiting_for_location = State()  # 6. Ожидание местоположения
    waiting_for_destination = State()  # 7. Ожидание региона назначения
    waiting_for_permit = State()  # 8. Ожидание информации о пропуске (динамически: Казань/Москва)
    waiting_for_crew = State()  # 9. Ожидание типа экипажа
    completed = State()  # Регистрация завершена

