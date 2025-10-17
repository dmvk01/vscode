import aiohttp
from typing import Optional
from sqlalchemy.orm import sessionmaker
from guide_ai_bot.app.db.models import User
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.core.config import settings
from guide_ai_bot.app.providers.mistral_provider import MistralProvider
from guide_ai_bot.app.providers.openrouter_provider import OpenRouterProvider


class AIService:
    def __init__(self):
        self.mistral_provider = MistralProvider()
        self.openrouter_provider = OpenRouterProvider()

    def _get_provider_by_subscription(self, subscription_type: str):
        """
        Фабричный метод для получения нужного провайдера в зависимости от подписки пользователя.
        """
        if subscription_type == "Premium":
            return self.openrouter_provider
        else:
            # Для Free и любых других значений используем Mistral
            return self.mistral_provider

    async def get_response(self, prompt: str, user_id: int) -> str:
        """
        Метод для получения ответа от ИИ.
        В зависимости от типа подписки пользователя (Free/Premium),
        использует соответствующий AI-провайдер.
        В случае ошибки основного провайдера, использует fallback-провайдер.
        """
        # Получаем информацию о пользователе из базы данных
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return "Ошибка: Пользователь не найден"

            # Получаем историю чата для контекста (последние 20 сообщений)
            chat_history = db.query(ChatHistory).filter(
                ChatHistory.user_id == user_id
            ).order_by(ChatHistory.timestamp.desc()).limit(20).all()
            
            # Формируем контекст из истории чата
            context = self._build_context(chat_history, prompt)
            
            # Получаем нужный провайдер в зависимости от подписки
            primary_provider = self._get_provider_by_subscription(user.subscription_type)
            
            # Для fallback используем противоположный провайдер
            fallback_provider = self.openrouter_provider if primary_provider == self.mistral_provider else self.mistral_provider

            # Сначала пробуем получить ответ от основного провайдера с контекстом
            result = await primary_provider.get_response(context)

            if result["status"] == "success":
                return result["response"]
            else:
                # Если основной провайдер не сработал, пробуем fallback
                print(f"Основной провайдер не сработал: {result['error']}. Пробуем fallback...")
                fallback_result = await fallback_provider.get_response(context)
                
                if fallback_result["status"] == "success":
                    return fallback_result["response"]
                else:
                    return f"Ошибка при обращении к основной и резервной моделям: {result['error']}; {fallback_result['error']}"

        except Exception as e:
            return f"Произошла ошибка: {str(e)}"
        finally:
            db.close()
    
    def _build_context(self, chat_history, current_prompt: str) -> str:
        """
        Формирует контекст из истории чата для передачи в ИИ
        """
        if not chat_history:
            return current_prompt
        
        # Разворачиваем историю, чтобы более старые сообщения были в начале
        chat_history.reverse()
        
        context_parts = ["Предыдущий контекст диалога:"]
        for entry in chat_history:
            if entry.message and entry.response:
                context_parts.append(f"Пользователь: {entry.message}")
                context_parts.append(f"Бот: {entry.response}")
        
        context_parts.append(f"Текущий вопрос пользователя: {current_prompt}")
        
        # Обрезаем контекст, если он слишком длинный (максимум 2000 символов)
        full_context = "\n".join(context_parts)
        if len(full_context) > 2000:
            # Если контекст слишком длинный, берем только вторую половину
            mid_point = len(full_context) // 2
            full_context = "Контекст (сокращен): ..." + full_context[mid_point:]
        
        return full_context