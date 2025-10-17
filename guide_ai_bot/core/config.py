# Конфигурация приложения
import os
from pydantic_settings import BaseSettings
from typing import Optional
from guide_ai_bot.app.db.settings_service import settings_service


class Settings(BaseSettings):
    # Переменные из .env файла
    bot_token: str
    database_url: str = "sqlite:///./guide_ai_bot.db"
    debug: bool = False
    mistral_api_key: str = ""
    mistral_model_name: str = ""
    openrouter_api_key: str = ""
    openrouter_model_name: str = ""
    ai_api_key: str = ""
    robokassa_login: str = ""
    robokassa_password1: str = ""
    robokassa_password2: str = ""
    robokassa_test_mode: bool = True
    robokassa_webhook_url: str = ""
    admin_username: str = "admin"
    admin_password: str = "admin123"
    
    def __init__(self, **data):
        # Пытаемся импортировать SessionLocal внутри метода, чтобы избежать циклического импорта
        try:
            from guide_ai_bot.app.db.session import SessionLocal
            # Загружаем настройки из базы данных с приоритетом над .env
            db_settings = settings_service.get_all_settings(SessionLocal)
            for key, value in db_settings.items():
                if hasattr(self, key):
                    # Преобразуем строковые значения в нужные типы
                    if key in ['debug', 'robokassa_test_mode']:
                        data[key] = value.lower() in ['true', '1', 'yes', 'on']
                    elif key in ['mistral_api_key', 'mistral_model_name', 'openrouter_api_key',
                               'openrouter_model_name', 'ai_api_key', 'robokassa_login',
                               'robokassa_password1', 'robokassa_password2', 'robokassa_webhook_url',
                               'admin_username', 'admin_password']:
                        data[key] = value
                    else:
                        data[key] = value
        except ImportError:
            # Если не удается импортировать SessionLocal, используем только .env
            pass
        
        super().__init__(**data)
    
    class Config:
        env_file = ".env"


# Глобальный объект конфигурации
# Загружаем настройки из базы данных в кэш при инициализации
try:
    from guide_ai_bot.app.db.session import SessionLocal
    settings_service.load_settings_to_cache(SessionLocal)
except ImportError:
    # Если не удается импортировать SessionLocal, пропускаем загрузку настроек из БД
    pass

settings = Settings()
