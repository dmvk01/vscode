from abc import ABC, abstractmethod
from aiogram import Router
from typing import Dict, Any, Optional
from sqlalchemy.orm import sessionmaker


class BaseModule(ABC):
    """
    Базовый класс для всех модулей бота.
    Определяет общий интерфейс для реализации различных функций бота.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.router = Router()
        self._setup_handlers()
    
    @abstractmethod
    def _setup_handlers(self):
        """
        Метод для настройки обработчиков команд и сообщений модуля
        """
        pass
    
    @abstractmethod
    async def execute(self, user_id: int, db: sessionmaker, **kwargs) -> Dict[str, Any]:
        """
        Основной метод выполнения модуля
        
        :param user_id: ID пользователя
        :param db: Сессия базы данных
        :param kwargs: Дополнительные параметры
        :return: Результат выполнения модуля
        """
        pass
    
    def get_router(self):
        """
        Возвращает роутер модуля для подключения к диспетчеру
        """
        return self.router