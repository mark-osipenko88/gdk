#!/usr/bin/env python3
"""
Главный файл для запуска MAX Chat Bot
"""

import sys
import os
import logging
import signal
from config import BotConfig
from max_chatbot import MAXChatBot
from utils import RateLimiter, UserSession, DatabaseManager, MessageFormatter

# Настройка логирования
def setup_logging(config: BotConfig):
    """Настройка системы логирования"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_extended_bot(config: BotConfig) -> MAXChatBot:
    """Создание расширенного бота с дополнительными функциями"""
    
    bot = MAXChatBot(config.BOT_TOKEN)
    bot.config = config
    
    # Инициализация дополнительных компонентов
    bot.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
    bot.user_sessions = UserSession(ttl_minutes=30)
    bot.database = DatabaseManager("bot_data.json")
    bot.formatter = MessageFormatter()
    
    # Добавление расширенных команд
    bot.add_command_handler("/admin", cmd_admin)
    bot.add_command_handler("/stats", cmd_stats)
    bot.add_command_handler("/weather", cmd_weather)
    bot.add_command_handler("/reminder", cmd_reminder)
    bot.add_command_handler("/calc", cmd_calculator)
    
    # Добавление обработчиков сообщений
    bot.add_message_handler(handle_stickers)
    bot.add_message_handler(handle_files)
    bot.add_message_handler(handle_urls)
    
    return bot

# Расширенные команды
def cmd_admin(bot_instance, chat_id: str, args: list, message: dict):
    """Административные команды"""
    user_id = str(message.get('from', {}).get('id', ''))
    
    if not bot_instance.config.is_admin(user_id):
        bot_instance.send_message(chat_id, "❌ У вас нет прав администратора.")
        return
    
    if not args:
        admin_help = """
🔧 Административные команды:

/admin stats - Статистика бота
/admin users - Список пользователей
/admin broadcast <сообщение> - Рассылка
/admin shutdown - Остановить бота
        """
        bot_instance.send_message(chat_id, admin_help.strip())
        return
    
    command = args[0].lower()
    
    if command == "stats":
        stats = bot_instance.database.get_global_data('stats', {})
        stats_text = f"""
📊 Статистика бота:

👥 Всего пользователей: {len(bot_instance.database.data.get('users', {}))}
💬 Сообщений обработано: {stats.get('messages_processed', 0)}
⚡ Команд выполнено: {stats.get('commands_executed', 0)}
🔄 Время работы: {stats.get('uptime', 'неизвестно')}
        """
        bot_instance.send_message(chat_id, stats_text.strip())
        
    elif command == "users":
        users = bot_instance.database.data.get('users', {})
        if users:
            user_list = "👥 Пользователи бота:\n\n"
            for user_id, user_data in list(users.items())[:10]:  # Показываем первых 10
                username = user_data.get('username', 'Unknown')
                user_list += f"• {username} (ID: {user_id})\n"
            if len(users) > 10:
                user_list += f"\n... и еще {len(users) - 10} пользователей"
        else:
            user_list = "Пользователей пока нет."
        
        bot_instance.send_message(chat_id, user_list)
        
    elif command == "broadcast" and len(args) > 1:
        broadcast_message = " ".join(args[1:])
        users = bot_instance.database.data.get('users', {})
        
        sent_count = 0
        for user_id in users:
            try:
                bot_instance.send_message(user_id, f"📢 Объявление:\n\n{broadcast_message}")
                sent_count += 1
            except:
                pass
        
        bot_instance.send_message(chat_id, f"✅ Рассылка отправлена {sent_count} пользователям.")
        
    elif command == "shutdown":
        bot_instance.send_message(chat_id, "🔄 Останавливаю бота...")
        bot_instance.stop()

def cmd_stats(bot_instance, chat_id: str, args: list, message: dict):
    """Команда статистики для пользователей"""
    user_id = str(message.get('from', {}).get('id', ''))
    user_data = bot_instance.database.get_user_data(user_id)
    
    stats_text = f"""
📈 Ваша статистика:

💬 Отправлено сообщений: {user_data.get('messages_sent', 0)}
⚡ Использовано команд: {user_data.get('commands_used', 0)}
📅 Первое сообщение: {user_data.get('first_seen', 'неизвестно')}
🕐 Последняя активность: {user_data.get('last_seen', 'сейчас')}
    """
    bot_instance.send_message(chat_id, stats_text.strip())

def cmd_weather(bot_instance, chat_id: str, args: list, message: dict):
    """Команда погоды (заглушка)"""
    if not args:
        bot_instance.send_message(chat_id, "Укажите город: /weather Москва")
        return
    
    city = " ".join(args)
    # Здесь должна быть интеграция с погодным API
    weather_text = f"""
🌤 Погода в {city}:

🌡 Температура: +15°C
💨 Ветер: 5 м/с, западный
💧 Влажность: 65%
☁ Облачность: переменная

(Это демо-данные. Подключите реальный API погоды)
    """
    bot_instance.send_message(chat_id, weather_text.strip())

def cmd_reminder(bot_instance, chat_id: str, args: list, message: dict):
    """Команда напоминания (заглушка)"""
    if len(args) < 2:
        bot_instance.send_message(chat_id, "Использование: /reminder 30m Купить молоко")
        return
    
    time_str = args[0]
    reminder_text = " ".join(args[1:])
    
    # Здесь должна быть логика создания напоминания
    bot_instance.send_message(chat_id, f"⏰ Напоминание '{reminder_text}' создано на {time_str}")

def cmd_calculator(bot_instance, chat_id: str, args: list, message: dict):
    """Простой калькулятор"""
    if not args:
        bot_instance.send_message(chat_id, "Использование: /calc 2+2 или /calc 10*5")
        return
    
    expression = "".join(args)
    
    try:
        # Безопасное вычисление только математических операций
        import re
        if not re.match(r'^[0-9+\-*/().\s]+$', expression):
            raise ValueError("Недопустимые символы")
        
        result = eval(expression)
        bot_instance.send_message(chat_id, f"🧮 {expression} = {result}")
        
    except Exception as e:
        bot_instance.send_message(chat_id, "❌ Ошибка в выражении. Проверьте синтаксис.")

# Дополнительные обработчики
def handle_stickers(chat_id: str, text: str, message: dict):
    """Обработка стикеров"""
    if message.get('sticker'):
        # Здесь можно добавить логику обработки стикеров
        pass

def handle_files(chat_id: str, text: str, message: dict):
    """Обработка файлов"""
    if message.get('document') or message.get('photo'):
        # Здесь можно добавить логику обработки файлов
        pass

def handle_urls(chat_id: str, text: str, message: dict):
    """Обработка URL в сообщениях"""
    import re
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    
    if urls:
        # Здесь можно добавить обработку найденных URL
        pass

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logging.info(f"Получен сигнал {signum}. Завершение работы...")
    sys.exit(0)

def main():
    """Главная функция"""
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Загрузка конфигурации
    config = BotConfig.from_env()
    
    # Проверка токена
    if config.BOT_TOKEN == "YOUR_TOKEN_HERE" or not config.BOT_TOKEN:
        print("❌ Ошибка: Не установлен токен бота!")
        print("Установите переменную окружения MAX_BOT_TOKEN или измените config.py")
        sys.exit(1)
    
    # Настройка логирования
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("🤖 Запуск MAX Chat Bot...")
    logger.info(f"Конфигурация: {config.API_BASE_URL}")
    
    try:
        # Создание и запуск бота
        bot = create_extended_bot(config)
        
        # Инициализация статистики
        stats = bot.database.get_global_data('stats', {})
        stats['bot_started'] = True
        bot.database.set_global_data('stats', stats)
        
        logger.info("✅ Бот готов к работе!")
        
        # Выбор режима запуска
        if config.WEBHOOK_URL:
            logger.info("Запуск в режиме webhook...")
            # Здесь должна быть логика для webhook сервера
            print("⚠️  Режим webhook требует дополнительной настройки веб-сервера")
        else:
            logger.info("Запуск в режиме polling...")
            bot.start_polling()
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки от пользователя")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    main()
