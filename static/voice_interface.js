// Клиентский JavaScript для голосового интерфейса с Web Speech API

// Подключение к серверу через Socket.IO
const socket = io();

// Элементы DOM
const messagesArea = document.getElementById('messages');
const voiceButton = document.getElementById('voiceButton');
const textInput = document.getElementById('textInput');
const sendButton = document.getElementById('sendButton');
const keyboardOptions = document.getElementById('keyboardOptions');
const listeningIndicator = document.getElementById('listeningIndicator');
const connectionStatus = document.getElementById('connectionStatus');
const speechStatus = document.getElementById('speechStatus');

// Web Speech API
let recognition = null;
let synthesis = window.speechSynthesis;
let isListening = false;

// Инициализация Speech Recognition (если поддерживается)
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = function () {
        isListening = true;
        voiceButton.classList.add('listening');
        listeningIndicator.classList.remove('hidden');
        speechStatus.textContent = '🎤 Слушаю...';
    };

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        console.log('Распознано:', transcript);
        sendMessage(transcript, true);
    };

    recognition.onerror = function (event) {
        console.error('Ошибка распознавания:', event.error);
        speechStatus.textContent = '❌ Ошибка: ' + event.error;
        stopListening();
    };

    recognition.onend = function () {
        stopListening();
    };
} else {
    speechStatus.textContent = '⚠️ Голосовой ввод не поддерживается';
    voiceButton.disabled = true;
}

function stopListening() {
    isListening = false;
    voiceButton.classList.remove('listening');
    listeningIndicator.classList.add('hidden');
    speechStatus.textContent = '';
}

// Обработчики событий
voiceButton.addEventListener('click', () => {
    if (!recognition) {
        alert('Голосовой ввод не поддерживается вашим браузером');
        return;
    }

    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
});

sendButton.addEventListener('click', () => {
    const text = textInput.value.trim();
    if (text) {
        sendMessage(text, false);
        textInput.value = '';
    }
});

textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendButton.click();
    }
});

// Функции отправки и получения сообщений
function sendMessage(text, isVoice) {
    // Добавляем сообщение пользователя в чат
    addMessage(text, 'user');

    // Отправляем на сервер
    socket.emit('user_message', {
        text: text,
        is_voice: isVoice
    });
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'bot' ? '🤖' : '👤';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    messagesArea.appendChild(messageDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function speak(text) {
    if (!synthesis) return;

    // Останавливаем предыдущее озвучивание
    synthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ru-RU';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = function () {
        speechStatus.textContent = '🔊 Говорю...';
    };

    utterance.onend = function () {
        speechStatus.textContent = '';
    };

    utterance.onerror = function (event) {
        console.error('Ошибка синтеза речи:', event.error);
        speechStatus.textContent = '';
    };

    synthesis.speak(utterance);
}

function showKeyboardOptions(options) {
    keyboardOptions.innerHTML = '';

    if (!options || options.length === 0) {
        keyboardOptions.classList.add('hidden');
        return;
    }

    keyboardOptions.classList.remove('hidden');

    options.forEach(option => {
        const button = document.createElement('button');
        button.className = 'keyboard-option';
        button.textContent = option;
        button.addEventListener('click', () => {
            sendMessage(option, false);
        });
        keyboardOptions.appendChild(button);
    });
}

// Socket.IO события
socket.on('connect', () => {
    console.log('Подключено к серверу');
    connectionStatus.textContent = '🟢 Подключено';
    connectionStatus.className = 'status connected';
});

socket.on('disconnect', () => {
    console.log('Отключено от сервера');
    connectionStatus.textContent = '🔴 Отключено';
    connectionStatus.className = 'status disconnected';
});

socket.on('bot_message', (data) => {
    console.log('Получено сообщение от бота:', data);

    // Добавляем сообщение в чат
    addMessage(data.text, 'bot');

    // Озвучиваем ответ
    speak(data.text);

    // Показываем опции клавиатуры, если есть
    if (data.keyboard_options) {
        showKeyboardOptions(data.keyboard_options);
    } else if (data.remove_keyboard) {
        showKeyboardOptions([]);
    }
});

// Инициализация
console.log('Голосовой интерфейс загружен');
