#!/usr/bin/env python3
"""
Тесты для MAX Chat Bot
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from max_chatbot import MAXChatBot
from config import BotConfig
from utils import RateLimiter, MessageFormatter, CommandParser, UserSession

class TestMAXChatBot(unittest.TestCase):
    """Тесты основного класса бота"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.bot = MAXChatBot("test_token")
        
    def test_bot_initialization(self):
        """Тест инициализации бота"""
        self.assertEqual(self.bot.token, "test_token")
        self.assertIsNotNone(self.bot.commands)
        self.assertIn("/start", self.bot.commands)
        self.assertIn("/help", self.bot.commands)
        
    def test_add_command_handler(self):
        """Тест добавления обработчика команд"""
        def test_command(chat_id, args, message):
            pass
            
        self.bot.add_command_handler("/test", test_command)
        self.assertIn("/test", self.bot.commands)
        self.assertEqual(self.bot.commands["/test"], test_command)
        
    def test_add_message_handler(self):
        """Тест добавления обработчика сообщений"""
        def test_handler(chat_id, text, message):
            pass
            
        initial_count = len(self.bot.message_handlers)
        self.bot.add_message_handler(test_handler)
        self.assertEqual(len(self.bot.message_handlers), initial_count + 1)
        
    @patch('requests.post')
    def test_send_message_success(self, mock_post):
        """Тест успешной отправки сообщения"""
        # Настройка мока
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Тест
        result = self.bot.send_message("123", "Test message")
        
        # Проверки
        self.assertTrue(result)
        mock_post.assert_called_once()
        
    @patch('requests.post')
    def test_send_message_failure(self, mock_post):
        """Тест неудачной отправки сообщения"""
        # Настройка мока
        mock_response = Mock()
        mock_response.json.return_value = {"ok": False, "description": "Error"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Тест
        result = self.bot.send_message("123", "Test message")
        
        # Проверки
        self.assertFalse(result)


class TestRateLimiter(unittest.TestCase):
    """Тесты ограничителя частоты запросов"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.limiter = RateLimiter(max_requests=2, window_seconds=1)
        
    def test_initial_request_allowed(self):
        """Тест разрешения первого запроса"""
        self.assertTrue(self.limiter.is_allowed("user1"))
        
    def test_multiple_requests_within_limit(self):
        """Тест множественных запросов в пределах лимита"""
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertTrue(self.limiter.is_allowed("user1"))
        
    def test_requests_exceeding_limit(self):
        """Тест превышения лимита запросов"""
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertFalse(self.limiter.is_allowed("user1"))
        
    def test_limit_reset_after_window(self):
        """Тест сброса лимита после окончания окна"""
        # Заполняем лимит
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertFalse(self.limiter.is_allowed("user1"))
        
        # Ждем окончания окна
        time.sleep(1.1)
        
        # Проверяем сброс лимита
        self.assertTrue(self.limiter.is_allowed("user1"))


class TestMessageFormatter(unittest.TestCase):
    """Тесты форматировщика сообщений"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.formatter = MessageFormatter()
        
    def test_short_text_no_split(self):
        """Тест короткого текста без разделения"""
        text = "Short message"
        result = self.formatter.format_text(text, max_length=100)
        self.assertEqual(result, [text])
        
    def test_long_text_split(self):
        """Тест разделения длинного текста"""
        text = "A" * 100
        result = self.formatter.format_text(text, max_length=50)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 50)
        self.assertEqual(len(result[1]), 50)
        
    def test_escape_markdown(self):
        """Тест экранирования markdown символов"""
        text = "*bold* _italic_ `code`"
        result = self.formatter.escape_markdown(text)
        self.assertNotIn("*", result.replace("\\*", ""))
        self.assertNotIn("_", result.replace("\\_", ""))
        self.assertNotIn("`", result.replace("\\`", ""))
        
    def test_format_code(self):
        """Тест форматирования кода"""
        code = "print('hello')"
        result = self.formatter.format_code(code, "python")
        self.assertTrue(result.startswith("```python"))
        self.assertTrue(result.endswith("```"))
        self.assertIn(code, result)
        
    def test_format_numbered_list(self):
        """Тест форматирования нумерованного списка"""
        items = ["First", "Second", "Third"]
        result = self.formatter.format_list(items, numbered=True)
        self.assertIn("1. First", result)
        self.assertIn("2. Second", result)
        self.assertIn("3. Third", result)
        
    def test_format_bullet_list(self):
        """Тест форматирования маркированного списка"""
        items = ["First", "Second", "Third"]
        result = self.formatter.format_list(items, numbered=False)
        self.assertIn("• First", result)
        self.assertIn("• Second", result)
        self.assertIn("• Third", result)


class TestCommandParser(unittest.TestCase):
    """Тесты парсера команд"""
    
    def test_simple_command(self):
        """Тест простой команды"""
        command, args, flags = CommandParser.parse_command("/start")
        self.assertEqual(command, "start")
        self.assertEqual(args, [])
        self.assertEqual(flags, {})
        
    def test_command_with_args(self):
        """Тест команды с аргументами"""
        command, args, flags = CommandParser.parse_command("/echo hello world")
        self.assertEqual(command, "echo")
        self.assertEqual(args, ["hello", "world"])
        self.assertEqual(flags, {})
        
    def test_command_with_flags(self):
        """Тест команды с флагами"""
        command, args, flags = CommandParser.parse_command("/search query --limit 10 -v")
        self.assertEqual(command, "search")
        self.assertEqual(args, ["query"])
        self.assertEqual(flags, {"limit": "10", "v": True})
        
    def test_non_command_text(self):
        """Тест обычного текста (не команды)"""
        command, args, flags = CommandParser.parse_command("regular text")
        self.assertEqual(command, "")
        self.assertEqual(args, [])
        self.assertEqual(flags, {})


class TestUserSession(unittest.TestCase):
    """Тесты пользовательских сессий"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.sessions = UserSession(ttl_minutes=1)
        
    def test_create_new_session(self):
        """Тест создания новой сессии"""
        session_data = self.sessions.get_session("user1")
        self.assertIsInstance(session_data, dict)
        self.assertEqual(len(session_data), 0)
        
    def test_set_and_get_session_data(self):
        """Тест установки и получения данных сессии"""
        self.sessions.set_session_data("user1", "key1", "value1")
        value = self.sessions.get_session_data("user1", "key1")
        self.assertEqual(value, "value1")
        
    def test_get_nonexistent_session_data(self):
        """Тест получения несуществующих данных сессии"""
        value = self.sessions.get_session_data("user1", "nonexistent", "default")
        self.assertEqual(value, "default")
        
    def test_clear_session(self):
        """Тест очистки сессии"""
        self.sessions.set_session_data("user1", "key1", "value1")
        self.sessions.clear_session("user1")
        value = self.sessions.get_session_data("user1", "key1", "default")
        self.assertEqual(value, "default")


class TestBotConfig(unittest.TestCase):
    """Тесты конфигурации бота"""
    
    def test_default_config(self):
        """Тест конфигурации по умолчанию"""
        config = BotConfig()
        self.assertEqual(config.REQUEST_TIMEOUT, 10)
        self.assertEqual(config.POLLING_TIMEOUT, 30)
        self.assertEqual(config.LOG_LEVEL, "INFO")
        self.assertEqual(config.ADMIN_IDS, [])
        
    def test_is_admin_check(self):
        """Тест проверки прав администратора"""
        config = BotConfig()
        config.ADMIN_IDS = ["123", "456"]
        
        self.assertTrue(config.is_admin("123"))
        self.assertTrue(config.is_admin("456"))
        self.assertFalse(config.is_admin("789"))


# Интеграционные тесты
class TestBotIntegration(unittest.TestCase):
    """Интеграционные тесты бота"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.bot = MAXChatBot("test_token")
        
    def test_process_start_command(self):
        """Тест обработки команды /start"""
        message = {
            "chat": {"id": "123"},
            "text": "/start",
            "message_id": 1,
            "from": {"username": "testuser", "id": 123}
        }
        
        with patch.object(self.bot, 'send_message') as mock_send:
            self.bot.process_message(message)
            mock_send.assert_called_once()
            
    def test_process_help_command(self):
        """Тест обработки команды /help"""
        message = {
            "chat": {"id": "123"},
            "text": "/help",
            "message_id": 1,
            "from": {"username": "testuser", "id": 123}
        }
        
        with patch.object(self.bot, 'send_message') as mock_send:
            self.bot.process_message(message)
            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            self.assertIn("команд", args[1].lower())
            
    def test_process_echo_command(self):
        """Тест обработки команды /echo"""
        message = {
            "chat": {"id": "123"},
            "text": "/echo hello world",
            "message_id": 1,
            "from": {"username": "testuser", "id": 123}
        }
        
        with patch.object(self.bot, 'send_message') as mock_send:
            self.bot.process_message(message)
            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            self.assertIn("hello world", args[1])
            
    def test_process_unknown_command(self):
        """Тест обработки неизвестной команды"""
        message = {
            "chat": {"id": "123"},
            "text": "/unknown",
            "message_id": 1,
            "from": {"username": "testuser", "id": 123}
        }
        
        with patch.object(self.bot, 'send_message') as mock_send:
            self.bot.process_message(message)
            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            self.assertIn("неизвестная", args[1].lower())


def run_tests():
    """Запуск всех тестов"""
    # Создаем test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    test_classes = [
        TestMAXChatBot,
        TestRateLimiter,
        TestMessageFormatter,
        TestCommandParser,
        TestUserSession,
        TestBotConfig,
        TestBotIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем результат
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Запуск тестов MAX Chat Bot...")
    print("=" * 50)
    
    success = run_tests()
    
    print("=" * 50)
    if success:
        print("✅ Все тесты прошли успешно!")
        exit(0)
    else:
        print("❌ Некоторые тесты провалились!")
        exit(1)
