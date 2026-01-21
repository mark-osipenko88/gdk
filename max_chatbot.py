
import json
import requests
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MAXChatBot:
    """
    Чат-бот для мессенджера MAX
    """
    
    def __init__(self, token: str, webhook_url: Optional[str] = None):
        self.token = token
        self.webhook_url = webhook_url
        self.base_url = "https://api.max-messenger.com/bot"  # Примерный URL API
        self.commands = {}
        self.message_handlers = []
        self.running = False
        
        # Регистрируем базовые команды
        self.register_default_commands()
        
    def register_default_commands(self):
        """Регистрация базовых команд"""
        self.add_command_handler("/start", self.cmd_start)
        self.add_command_handler("/help", self.cmd_help)
        self.add_command_handler("/time", self.cmd_time)
        self.add_command_handler("/echo", self.cmd_echo)
        self.add_command_handler("/info", self.cmd_info)
        
    def add_command_handler(self, command: str, handler):
        """Добавление обработчика команды"""
        self.commands[command.lower()] = handler
        logger.info(f"Зарегистрирована команда: {command}")
        
    def add_message_handler(self, handler):
        """Добавление обработчика сообщений"""
        self.message_handlers.append(handler)
        
    def send_message(self, chat_id: str, text: str, reply_to: Optional[str] = None) -> bool:
        """Отправка сообщения"""
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "token": self.token
        }
        
        if reply_to:
            payload["reply_to_message_id"] = reply_to
            
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info(f"Сообщение отправлено в чат {chat_id}")
                return True
            else:
                logger.error(f"Ошибка отправки: {result.get('description')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HTTP запроса: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return False
            
    def send_photo(self, chat_id: str, photo_url: str, caption: str = "") -> bool:
        """Отправка фотографии"""
        url = f"{self.base_url}/sendPhoto"
        
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption,
            "token": self.token
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info(f"Фото отправлено в чат {chat_id}")
                return True
            else:
                logger.error(f"Ошибка отправки фото: {result.get('description')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HTTP запроса: {e}")
            return False
            
    def get_updates(self, offset: int = 0) -> List[Dict]:
        """Получение обновлений (polling)"""
        url = f"{self.base_url}/getUpdates"
        
        params = {
            "token": self.token,
            "offset": offset,
            "limit": 100,
            "timeout": 30
        }
        
        try:
            response = requests.get(url, params=params, timeout=35)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                return result.get("result", [])
            else:
                logger.error(f"Ошибка получения обновлений: {result.get('description')}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения обновлений: {e}")
            return []
            
    def process_message(self, message: Dict):
        """Обработка входящего сообщения"""
        try:
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            message_id = message.get("message_id")
            user = message.get("from", {})
            
            if not chat_id:
                return
                
            logger.info(f"Получено сообщение от {user.get('username', 'Unknown')}: {text}")
            
            # Проверяем команды
            if text.startswith("/"):
                command_parts = text.split()
                command = command_parts[0].lower()
                args = command_parts[1:] if len(command_parts) > 1 else []
                
                if command in self.commands:
                    try:
                        self.commands[command](chat_id, args, message)
                    except Exception as e:
                        logger.error(f"Ошибка выполнения команды {command}: {e}")
                        self.send_message(chat_id, "Произошла ошибка при выполнении команды.")
                else:
                    self.send_message(chat_id, f"Неизвестная команда: {command}\nИспользуйте /help для списка команд.")
            else:
                # Обрабатываем обычные сообщения
                for handler in self.message_handlers:
                    try:
                        handler(chat_id, text, message)
                    except Exception as e:
                        logger.error(f"Ошибка в обработчике сообщений: {e}")
                        
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            
    # Команды бота
    def cmd_start(self, chat_id: str, args: List[str], message: Dict):
        """Команда /start"""
        welcome_text = """
🤖 Добро пожаловать!

Я бот для мессенджера MAX.
Используйте /help чтобы увидеть список доступных команд.

Готов к работе! 🚀
        """
        self.send_message(chat_id, welcome_text.strip())
        
    def cmd_help(self, chat_id: str, args: List[str], message: Dict):
        """Команда /help"""
        help_text = """
📋 Доступные команды:

/start - Запустить бота
/help - Показать это сообщение
/time - Показать текущее время
/echo <текст> - Повторить ваш текст
/info - Информация о боте

🔧 Дополнительные функции:
• Отвечает на обычные сообщения
• Поддерживает отправку изображений
• Логирование всех действий
        """
        self.send_message(chat_id, help_text.strip())
        
    def cmd_time(self, chat_id: str, args: List[str], message: Dict):
        """Команда /time"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.send_message(chat_id, f"🕐 Текущее время: {current_time}")
        
    def cmd_echo(self, chat_id: str, args: List[str], message: Dict):
        """Команда /echo"""
        if args:
            echo_text = " ".join(args)
            self.send_message(chat_id, f"🔊 Эхо: {echo_text}")
        else:
            self.send_message(chat_id, "Используйте: /echo <ваш текст>")
            
    def cmd_info(self, chat_id: str, args: List[str], message: Dict):
        """Команда /info"""
        info_text = """
ℹ️ Информация о боте:

🤖 Название: MAX Chat Bot
📅 Версия: 1.0.0
🐍 Python: 3.8+
⚡ Статус: Активен

Разработано для мессенджера MAX
        """
        self.send_message(chat_id, info_text.strip())
        
    def start_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Запуск бота в режиме polling...")
        self.running = True
        offset = 0
        
        while self.running:
            try:
                updates = self.get_updates(offset)
                
                for update in updates:
                    offset = update.get("update_id", 0) + 1
                    
                    if "message" in update:
                        self.process_message(update["message"])
                        
                if not updates:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки...")
                break
            except Exception as e:
                logger.error(f"Ошибка в polling: {e}")
                time.sleep(5)
                
        self.running = False
        logger.info("Бот остановлен")
        
    def stop(self):
        """Остановка бота"""
        self.running = False
        
    def set_webhook(self, url: str) -> bool:
        """Установка webhook"""
        webhook_url = f"{self.base_url}/setWebhook"
        
        payload = {
            "url": url,
            "token": self.token
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info(f"Webhook установлен: {url}")
                return True
            else:
                logger.error(f"Ошибка установки webhook: {result.get('description')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка установки webhook: {e}")
            return False


# Дополнительные обработчики сообщений
def handle_greeting(chat_id: str, text: str, message: Dict):
    """Обработчик приветствий"""
    greetings = ["привет", "hello", "hi", "здравствуй", "добрый день"]
    
    if any(greeting in text.lower() for greeting in greetings):
        bot.send_message(chat_id, "👋 Привет! Как дела?")


def handle_questions(chat_id: str, text: str, message: Dict):
    """Обработчик вопросов"""
    questions = ["как дела", "что делаешь", "как жизнь"]
    
    if any(question in text.lower() for question in questions):
        responses = [
            "Всё отлично! Готов помочь! 😊",
            "Дела идут хорошо, спасибо за вопрос! 👍",
            "Работаю и жду ваших команд! 🤖"
        ]
        import random
        bot.send_message(chat_id, random.choice(responses))


# Создание экземпляра бота (пример использования)
if __name__ == "__main__":
    # Замените на ваш реальный токен от MAX API
    BOT_TOKEN = "YOUR_MAX_BOT_TOKEN_HERE"
    
    # Создаем бота
    bot = MAXChatBot(BOT_TOKEN)
    
    # Добавляем дополнительные обработчики
    bot.add_message_handler(handle_greeting)
    bot.add_message_handler(handle_questions)
    
    # Запускаем бота
    try:
        bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
        bot.stop()
