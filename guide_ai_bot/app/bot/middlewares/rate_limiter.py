from typing import Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from guide_ai_bot.utils.security import RateLimiter


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, max_requests: int = 10, time_window: int = 60, max_voice_requests: int = 5, voice_time_window: int = 60):
        super().__init__()
        self.rate_limiter = RateLimiter(max_requests, time_window, max_voice_requests, voice_time_window)

    async def __call__(
        self,
        handler: Callable,
        event: Message,
        data: dict
    ) -> Awaitable:
        # Проверяем, является ли событие сообщением
        if isinstance(event, Message):
            user_id = event.from_user.id
            
            # Определяем тип запроса (голосовой или текстовый)
            is_voice = hasattr(event, 'voice') and event.voice is not None
            
            # Проверяем, разрешен ли запрос
            if not self.rate_limiter.is_allowed(user_id, is_voice):
                if is_voice:
                    await event.answer("Слишком много голосовых запросов. Пожалуйста, подождите немного перед отправкой следующего голосового сообщения.")
                else:
                    await event.answer("Слишком много запросов. Пожалуйста, подождите немного перед отправкой следующего сообщения.")
                return
        
        # Пропускаем событие дальше
        return await handler(event, data)