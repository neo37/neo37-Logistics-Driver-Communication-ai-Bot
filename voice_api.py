"""Flask приложение для голосового интерфейса бота с использованием Web Speech API"""
import asyncio
import logging
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS

from service_layer import VehicleRegistrationService, UserResponse, RegistrationStep
from interfaces.voice_adapter import VoiceAdapter
from interfaces.base_interface import InterfaceMessage
from config import API_HOST, API_PORT

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # В продакшене использовать из .env
CORS(app)

# Инициализация SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Инициализация сервисов
registration_service = VehicleRegistrationService()
voice_adapter = VoiceAdapter(socketio)


@app.route('/')
def index():
    """Главная страница - голосовой интерфейс"""
    return render_template('voice_interface.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'voice-interface'}, 200


@socketio.on('connect')
def handle_connect():
    """Обработка подключения нового пользователя"""
    session_id = request.sid
    join_room(session_id)
    logger.info(f"User connected: {session_id}")
    
    # Отправляем приветственное сообщение
    emit('bot_message', {
        'text': 'Добро пожаловать в голосовой интерфейс регистрации транспортных средств! Скажите "начать" для начала регистрации.',
        'keyboard_options': ['Начать', 'Помощь']
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения пользователя"""
    session_id = request.sid
    logger.info(f"User disconnected: {session_id}")


@socketio.on('user_message')
def handle_user_message(data):
    """
    Обработка сообщения от пользователя
    
    Args:
        data: {'text': 'текст сообщения', 'is_voice': True/False}
    """
    session_id = request.sid
    user_text = data.get('text', '').strip()
    is_voice = data.get('is_voice', False)
    
    logger.info(f"Received message from {session_id}: {user_text} (voice: {is_voice})")
    
    # Получаем данные сессии
    session_data = asyncio.run(voice_adapter.get_user_session_data(session_id))
    current_step = session_data.get('current_step')
    
    # Обработка команд
    if user_text.lower() in ['начать', 'start', '/start']:
        asyncio.run(handle_start_registration(session_id))
        return
    
    if user_text.lower() in ['помощь', 'help', '/help']:
        asyncio.run(handle_help(session_id))
        return
    
    # Если пользователь в процессе регистрации
    if current_step:
        asyncio.run(handle_registration_step(session_id, user_text, session_data, current_step))
    else:
        # Пользователь не в процессе регистрации
        emit('bot_message', {
            'text': 'Для начала регистрации скажите "начать"',
            'keyboard_options': ['Начать', 'Помощь']
        })


async def handle_start_registration(session_id: str):
    """Начать новую регистрацию"""
    # Очищаем старую сессию
    await voice_adapter.clear_user_session(session_id)
    
    # Начинаем новую регистрацию
    response = await registration_service.start_registration(
        user_id=hash(session_id),  # Используем хеш session_id как user_id
        username=session_id
    )
    
    # Сохраняем vehicle_id и текущий шаг в сессии
    await voice_adapter.update_user_session_data(session_id, {
        'vehicle_id': hash(session_id),  # Временно, нужно получить real vehicle_id
        'current_step': response.next_step.value if response.next_step else None
    })
    
    # Отправляем ответ пользователю
    message = InterfaceMessage(
        text=response.message,
        keyboard_options=response.keyboard_options,
        remove_keyboard=response.is_completed
    )
    await voice_adapter.send_message(session_id, message)


async def handle_help(session_id: str):
    """Показать помощь"""
    help_text = await registration_service.get_help_text()
    message = InterfaceMessage(text=help_text)
    await voice_adapter.send_message(session_id, message)


async def handle_registration_step(session_id: str, user_text: str, session_data: dict, current_step_value: str):
    """Обработка шага регистрации"""
    try:
        current_step = RegistrationStep(current_step_value)
    except ValueError:
        logger.error(f"Invalid step value: {current_step_value}")
        return
    
    # Создаем объект ответа пользователя
    user_response = UserResponse(
        text=user_text,
        user_id=hash(session_id),
        session_data=session_data
    )
    
    # Обрабатываем шаг
    bot_response = await registration_service.process_step(user_response, current_step)
    
    # Обновляем сессию
    if bot_response.next_step:
        await voice_adapter.update_user_session_data(session_id, {
            'current_step': bot_response.next_step.value
        })
    
    # Если регистрация завершена, очищаем сессию
    if bot_response.is_completed:
        await voice_adapter.clear_user_session(session_id)
    
    # Отправляем ответ пользователю
    message = InterfaceMessage(
        text=bot_response.message,
        keyboard_options=bot_response.keyboard_options,
        remove_keyboard=bot_response.is_completed
    )
    await voice_adapter.send_message(session_id, message)


def run_voice_api(host=None, port=None):
    """Запустить голосовой API сервер"""
    host = host or API_HOST
    port = port or API_PORT + 1  # Используем порт на 1 больше, чем основной API
    
    logger.info(f"Starting Voice API server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=True)


if __name__ == '__main__':
    run_voice_api()
