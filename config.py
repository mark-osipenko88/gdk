
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class BotConfig:
    """Конфигурация бота"""
    
    # Токен бота MAX (получите в настройках бота)
    BOT_TOKEN: str = os.getenv("MAX_BOT_TOKEN", "YOUR_TOKEN_HERE")
    
    # URL для webhook (если используется)
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    
    # Настройки API
    API_BASE_URL: str = "https://api.max-messenger.com/bot"
    REQUEST_TIMEOUT: int = 10
    POLLING_TIMEOUT: int = 30
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "bot.log"
    
    # Настройки бота
    MAX_MESSAGE_LENGTH: int = 4096
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: int = 5
    
    # Админы бота (ID пользователей)
    ADMIN_IDS: list = None
    
    def __post_init__(self):
        if self.ADMIN_IDS is None:
            self.ADMIN_IDS = []
            
    @classmethod
    def from_env(cls):
        """Создание конфигурации из переменных окружения"""
        return cls()
        
    def is_admin(self, user_id: str) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.ADMIN_IDS
