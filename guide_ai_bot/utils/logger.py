import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Кастомный форматер для логирования в формате JSON
    """
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Добавляем дополнительные поля, если они есть
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        # Добавляем информацию об исключении, если оно есть
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Настраивает и возвращает логгер с JSON-форматированием и ротацией файлов
    """
    # Создаем папку для логов, если она не существует
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Избегаем дублирования хендлеров
    if logger.handlers:
        return logger
    
    # Создаем форматер
    json_formatter = JSONFormatter()
    
    # Настройка файла для логов
    log_file = logs_dir / "app.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(json_formatter)
    
    # Настройка консольного логирования
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(json_formatter)
    
    # Добавляем хендлеры к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Возвращает логгер с предустановленной конфигурацией
    """
    return setup_logger(name)


# Инициализация корневого логгера
root_logger = setup_logger("guide_ai_bot", logging.INFO)