from typing import Dict, Type, Optional
from aiogram import Router
from guide_ai_bot.app.bot.modules.base_module import BaseModule


class ModuleLoader:
    """
    Утилита для динамической загрузки и регистрации модулей
    """
    
    def __init__(self):
        self.modules: Dict[str, BaseModule] = {}
        self.routers: Dict[str, Router] = {}
    
    def register_module(self, module: BaseModule):
        """
        Регистрирует модуль в системе
        """
        self.modules[module.name] = module
        self.routers[module.name] = module.get_router()
        print(f"Модуль '{module.name}' зарегистрирован")
    
    def get_module(self, name: str) -> Optional[BaseModule]:
        """
        Возвращает зарегистрированный модуль по имени
        """
        return self.modules.get(name)
    
    def get_router(self, name: str) -> Optional[Router]:
        """
        Возвращает роутер модуля по имени
        """
        return self.routers.get(name)
    
    def get_all_modules(self) -> Dict[str, BaseModule]:
        """
        Возвращает все зарегистрированные модули
        """
        return self.modules.copy()
    
    def load_default_modules(self):
        """
        Загружает и регистрирует стандартные модули
        """
        # Импортируем модули (в реальном приложении это может быть динамический импорт)
        from guide_ai_bot.app.bot.modules.quiz_module import QuizModule
        from guide_ai_bot.app.bot.modules.translate_module import TranslateModule
        
        # Регистрируем модули
        self.register_module(QuizModule())
        self.register_module(TranslateModule())


# Глобальный экземпляр загрузчика модулей
module_loader = ModuleLoader()