#!/usr/bin/env python3
"""
Webhook сервер для MAX Chat Bot
Используется для получения сообщений через webhook вместо polling
"""

from flask import Flask, request, jsonify
import json
import logging
import threading
from config import BotConfig
from max_chatbot import MAXChatBot
from utils import WebhookValidator

app = Flask(__name__)
bot = None
config = None
validator = None

def setup_webhook_bot():
    """Настройка бота для webhook режима"""
    global bot, config, validator
    
    config = BotConfig.from_env()
    bot = MAXChatBot(config.BOT_TOKEN)
    validator = WebhookValidator(config.BOT_TOKEN)
    
    # Настройка логирования
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    return bot

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик webhook запросов"""
    try:
        # Проверка валидности запроса
        if validator and not validator.validate_request(dict(request.headers), request.data):
            return jsonify({'error': 'Invalid signature'}), 403
        
        # Получение данных
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Обработка обновления в отдельном потоке
        if 'message' in data:
            threading.Thread(
                target=bot.process_message,
                args=(data['message'],)
            ).start()
        
        return jsonify({'ok': True}), 200
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервера"""
    return jsonify({
        'status': 'ok',
        'bot_running': bot is not None,
        'timestamp': int(time.time())
    }), 200

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Установка webhook URL"""
    try:
        webhook_url = request.json.get('url')
        if not webhook_url:
            return jsonify({'error': 'URL required'}), 400
        
        if bot.set_webhook(webhook_url):
            return jsonify({'ok': True, 'message': 'Webhook set successfully'})
        else:
            return jsonify({'error': 'Failed to set webhook'}), 500
            
    except Exception as e:
        logging.error(f"Set webhook error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import time
    
    # Инициализация бота
    setup_webhook_bot()
    
    # Запуск Flask сервера
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )
