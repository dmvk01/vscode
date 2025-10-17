from sqlalchemy.orm import sessionmaker
from typing import Optional, Dict, Any
from guide_ai_bot.app.db.models import Setting
from guide_ai_bot.utils.logger import get_logger


class SettingsService:
    """
    Сервис для работы с настройками из базы данных
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._cache: Dict[str, str] = {}
        self._cache_enabled = True
    
    def get_setting(self, key: str, default: Optional[str] = None, SessionLocal=None) -> Optional[str]:
        """
        Получает значение настройки по ключу
        
        :param key: Ключ настройки
        :param default: Значение по умолчанию, если настройка не найдена
        :param SessionLocal: Фабрика сессий SQLAlchemy (опционально)
        :return: Значение настройки или значение по умолчанию
        """
        # Проверяем кэш
        if self._cache_enabled and key in self._cache:
            return self._cache[key]
        
        # Если SessionLocal не передан, возвращаем значение по умолчанию
        if SessionLocal is None:
            return default
        
        db: sessionmaker = SessionLocal()
        try:
            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                # Сохраняем в кэш
                if self._cache_enabled:
                    self._cache[key] = setting.value
                return setting.value
            else:
                return default
        except Exception as e:
            self.logger.error(f"Ошибка при получении настройки {key}: {str(e)}")
            return default
        finally:
            db.close()
    
    def set_setting(self, key: str, value: str, description: Optional[str] = None, SessionLocal=None) -> bool:
        """
        Устанавливает значение настройки
        
        :param key: Ключ настройки
        :param value: Значение настройки
        :param description: Описание настройки
        :param SessionLocal: Фабрика сессий SQLAlchemy (опционально)
        :return: True, если настройка успешно установлена
        """
        # Если SessionLocal не передан, возвращаем False
        if SessionLocal is None:
            self.logger.error("SessionLocal не передан в set_setting")
            return False
        
        db: sessionmaker = SessionLocal()
        try:
            # Проверяем, существует ли настройка
            setting = db.query(Setting).filter(Setting.key == key).first()
            
            if setting:
                # Обновляем существующую настройку
                setting.value = value
                if description:
                    setting.description = description
            else:
                # Создаем новую настройку
                setting = Setting(key=key, value=value, description=description)
                db.add(setting)
            
            db.commit()
            
            # Обновляем кэш
            if self._cache_enabled:
                self._cache[key] = value
            
            self.logger.info(f"Настройка {key} успешно установлена")
            return True
        except Exception as e:
            db.rollback()
            self.logger.error(f"Ошибка при установке настройки {key}: {str(e)}")
            return False
        finally:
            db.close()
    
    def delete_setting(self, key: str, SessionLocal=None) -> bool:
        """
        Удаляет настройку по ключу
        
        :param key: Ключ настройки
        :param SessionLocal: Фабрика сессий SQLAlchemy (опционально)
        :return: True, если настройка успешно удалена
        """
        # Если SessionLocal не передан, возвращаем False
        if SessionLocal is None:
            self.logger.error("SessionLocal не передан в delete_setting")
            return False
        
        db: sessionmaker = SessionLocal()
        try:
            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                db.delete(setting)
                db.commit()
                
                # Удаляем из кэша
                if self._cache_enabled and key in self._cache:
                    del self._cache[key]
                
                self.logger.info(f"Настройка {key} успешно удалена")
                return True
            else:
                return False
        except Exception as e:
            db.rollback()
            self.logger.error(f"Ошибка при удалении настройки {key}: {str(e)}")
            return False
        finally:
            db.close()
    
    def get_all_settings(self, SessionLocal=None) -> Dict[str, str]:
        """
        Получает все настройки
        
        :param SessionLocal: Фабрика сессий SQLAlchemy (опционально)
        :return: Словарь всех настроек
        """
        # Если SessionLocal не передан, возвращаем пустой словарь
        if SessionLocal is None:
            self.logger.error("SessionLocal не передан в get_all_settings")
            return {}
        
        db: sessionmaker = SessionLocal()
        try:
            settings = db.query(Setting).all()
            return {setting.key: setting.value for setting in settings}
        except Exception as e:
            self.logger.error(f"Ошибка при получении всех настроек: {str(e)}")
            return {}
        finally:
            db.close()
    
    def load_settings_to_cache(self, SessionLocal=None):
        """
        Загружает все настройки в кэш
        
        :param SessionLocal: Фабрика сессий SQLAlchemy (опционально)
        """
        if not self._cache_enabled:
            return
        
        # Если SessionLocal не передан, ничего не делаем
        if SessionLocal is None:
            self.logger.error("SessionLocal не передан в load_settings_to_cache")
            return
        
        db: sessionmaker = SessionLocal()
        try:
            settings = db.query(Setting).all()
            self._cache = {setting.key: setting.value for setting in settings}
            self.logger.info(f"В кэш загружено {len(self._cache)} настроек")
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке настроек в кэш: {str(e)}")
        finally:
            db.close()
    
    def clear_cache(self):
        """
        Очищает кэш настроек
        """
        self._cache.clear()
        self.logger.info("Кэш настроек очищен")
    
    def enable_cache(self):
        """
        Включает кэширование настроек
        """
        self._cache_enabled = True
        self.logger.info("Кэширование настроек включено")
    
    def disable_cache(self):
        """
        Выключает кэширование настроек
        """
        self._cache_enabled = False
        self.clear_cache()
        self.logger.info("Кэширование настроек выключено")


# Глобальный экземпляр сервиса настроек
settings_service = SettingsService()