import re
from typing import Dict, Set
from datetime import datetime, timedelta
from collections import defaultdict


class RateLimiter:
    """
    Класс для ограничения частоты запросов (Rate Limiting)
    """
    def __init__(self, max_requests: int = 10, time_window: int = 60, max_voice_requests: int = 5, voice_time_window: int = 60):
        """
        :param max_requests: Максимальное количество обычных запросов
        :param time_window: Временное окно в секундах для обычных запросов
        :param max_voice_requests: Максимальное количество голосовых запросов
        :param voice_time_window: Временное окно в секундах для голосовых запросов
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.max_voice_requests = max_voice_requests
        self.voice_time_window = voice_time_window
        self.requests: Dict[int, list] = defaultdict(list)  # user_id: список временных меток для обычных запросов
        self.voice_requests: Dict[int, list] = defaultdict(list)  # user_id: список временных меток для голосовых запросов

    def is_allowed(self, user_id: int, is_voice: bool = False) -> bool:
        """
        Проверяет, разрешен ли запрос для пользователя
        :param user_id: ID пользователя
        :param is_voice: Является ли запрос голосовым
        """
        now = datetime.now()
        
        if is_voice:
            # Проверяем лимит для голосовых запросов
            # Удаляем старые записи, которые вышли за пределы временного окна
            self.voice_requests[user_id] = [
                timestamp for timestamp in self.voice_requests[user_id]
                if now - timestamp < timedelta(seconds=self.voice_time_window)
            ]
            
            # Проверяем, не превышено ли максимальное количество голосовых запросов
            if len(self.voice_requests[user_id]) >= self.max_voice_requests:
                return False
            
            # Добавляем текущий голосовой запрос
            self.voice_requests[user_id].append(now)
        else:
            # Проверяем лимит для обычных запросов
            # Удаляем старые записи, которые вышли за пределы временного окна
            self.requests[user_id] = [
                timestamp for timestamp in self.requests[user_id]
                if now - timestamp < timedelta(seconds=self.time_window)
            ]
            
            # Проверяем, не превышено ли максимальное количество запросов
            if len(self.requests[user_id]) >= self.max_requests:
                return False
            
            # Добавляем текущий запрос
            self.requests[user_id].append(now)
        
        return True


class InputModerator:
    """
    Класс для модерации ввода пользователя
    """
    def __init__(self):
        # Список потенциально опасных паттернов
        self.dangerous_patterns = [
            r'<script.*?>.*?</script>',  # HTML-скрипты
            r'javascript:',              # JavaScript URL
            r'vbscript:',               # VBScript URL
            r'on\w+\s*=',               # HTML-события (onclick, onload и т.д.)
            r'<iframe.*?>',             # iframe
            r'<object.*?>',             # object
            r'<embed.*?>',              # embed
            r'<form.*?>',               # form
            r'<link.*?>',               # link теги
            r'<meta.*?>',               # meta теги
            r'eval\s*\(',               # eval функция
            r'expression\s*\(',         # expression функция
            r'exec\s*\(',               # exec функция
            r'execfile\s*\(',           # execfile функция
            r'file\s*\(',               # file функция
            r'open\s*\(',               # open функция
            r'import\s+',               # import команды
            r'__import__\s*\(',         # __import__ функция
            r'os\.',                    # os модуль
            r'sys\.',                   # sys модуль
            r'subprocess\.',            # subprocess модуль
            r'pickle\.',                # pickle модуль
            r'importlib\.',             # importlib модуль
            r'codecs\.',                # codecs модуль
            r'exec\(',                  # exec команды
            r'eval\(',                  # eval команды
            r'input\(',                 # input команды
            r'raw_input\(',             # raw_input команды
            r'__.*?__',                 # dunder методы
            r'globals\(\)',             # globals функция
            r'locals\(\)',              # locals функция
            r'compile\(',               # compile функция
            r'apply\(',                 # apply функция
            r'call\(',                  # call функция
            r'getattr\(',               # getattr функция
            r'setattr\(',               # setattr функция
            r'delattr\(',               # delattr функция
            r'hasattr\(',               # hasattr функция
            r'execfile\(',              # execfile функция
        ]
        
        # Компилируем регулярные выражения для более эффективного поиска
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.dangerous_patterns]
    
    def is_safe_input(self, text: str) -> bool:
        """
        Проверяет, является ли ввод безопасным
        """
        if not text or not isinstance(text, str):
            return False
        
        # Проверяем каждый паттерн
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return False
        
        return True
    
    def moderate_input(self, text: str) -> tuple[bool, str]:
        """
        Модерирует ввод и возвращает кортеж (безопасно, сообщение об ошибке)
        """
        if not self.is_safe_input(text):
            return False, "Ваше сообщение содержит потенциально опасный контент и не может быть обработано."
        
        return True, ""