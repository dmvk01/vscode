from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any

from guide_ai_bot.app.bot.modules.base_module import BaseModule
from guide_ai_bot.app.db.models import User
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.app.services.ai_service import AIService
from guide_ai_bot.utils.logger import get_logger


class TranslateModule(BaseModule):
    """
    Модуль переводчика
    """
    
    def __init__(self):
        super().__init__("translate", "Переводчик")
        self.logger = get_logger(__name__)
        self.supported_languages = {
            "en": "Английский",
            "ru": "Русский", 
            "es": "Испанский",
            "fr": "Французский",
            "de": "Немецкий",
            "it": "Итальянский"
        }
    
    def _setup_handlers(self):
        """
        Настраивает обработчики команд и сообщений модуля
        """
        @self.router.message(Command("translate"))
        async def translate_command_handler(message: types.Message):
            await self._start_translation(message)
    
    async def _start_translation(self, message: types.Message):
        """
        Начинает процесс перевода
        """
        user_id = message.from_user.id
        
        # Создаем сессию для работы с базой данных
        db: sessionmaker = SessionLocal()
        
        try:
            # Получаем пользователя из базы данных
            user = db.query(User).filter(User.user_id == user_id).first()
            
            if not user:
                await message.answer("Ошибка: Пользователь не найден")
                return
            
            # Проверяем, предоставлено ли согласие на обработку данных
            if user.consent is None or user.consent is False:
                consent_message = (
                    "Для использования этой функции, пожалуйста, подтвердите согласие "
                    "на обработку персональных данных с помощью команды /start."
                )
                await message.answer(consent_message)
                return
            
            # Проверяем, есть ли активный модуль у пользователя
            if user.current_module and user.current_module != 'chat':
                await message.answer(f"Вы уже используете модуль: {user.current_module}. Сначала завершите его с помощью /back.")
                return
            
            # Устанавливаем текущий модуль как 'translate'
            user.current_module = 'translate'
            db.commit()
            
            # Отправляем инструкции по использованию
            languages_list = ", ".join([f"{code} ({name})" for code, name in self.supported_languages.items()])
            instructions = (
                "Модуль переводчика активирован 🌍\n\n"
                "Для перевода текста просто отправьте сообщение с текстом, который нужно перевести.\n\n"
                f"Поддерживаемые языки: {languages_list}\n\n"
                "Чтобы указать язык перевода, начните сообщение с кода языка (например, 'en Hello world').\n"
                "Для выхода из модуля используйте команду /back"
            )
            
            await message.answer(instructions)
            
        finally:
            # Закрываем сессию
            db.close()
    
    async def execute(self, user_id: int, db: sessionmaker, user_message: str = None, target_language: str = "en", **kwargs) -> Dict[str, Any]:
        """
        Выполняет перевод текста
        """
        try:
            if not user_message:
                return {"status": "error", "message": "Не указан текст для перевода"}
            
            # Подготавливаем запрос для ИИ
            prompt = f"Переведи следующий текст на {self.supported_languages.get(target_language, 'английский')} язык: {user_message}"
            
            # Получаем экземпляр AI сервиса (передаем как параметр)
            ai_service = kwargs.get("ai_service")
            if not ai_service:
                return {"status": "error", "message": "AI сервис не передан"}
            
            # Получаем перевод от ИИ
            translation = await ai_service.get_response(prompt, user_id)
            
            result = {
                "status": "success",
                "original_text": user_message,
                "translated_text": translation,
                "target_language": target_language
            }
            
            self.logger.info(f"Выполнен перевод для пользователя {user_id}", extra={'user_id': user_id})
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка в модуле перевода: {str(e)}", extra={'user_id': user_id, 'error_type': type(e).__name__})
            return {"status": "error", "message": f"Ошибка при выполнении перевода: {str(e)}"}
    
    async def continue_translation(self, message: types.Message, ai_service: AIService):
        """
        Продолжение обработки текста для перевода
        """
        user_id = message.from_user.id
        user_text = message.text.strip()
        
        db: sessionmaker = SessionLocal()
        
        try:
            # Проверяем, что пользователь находится в модуле перевода
            user = db.query(User).filter(User.user_id == user_id).first()
            
            if user.current_module != 'translate':
                return
            
            # Определяем язык перевода из сообщения (если указан)
            target_language = "en" # по умолчанию
            words = user_text.split(" ", 1)
            
            if len(words) > 1 and words[0].lower() in self.supported_languages:
                target_language = words[0].lower()
                user_text = words[1]
            
            # Выполняем перевод
            result = await self.execute(user_id, db, user_message=user_text, target_language=target_language, ai_service=ai_service)
            
            if result["status"] == "success":
                response = f"📖 Перевод:\n\n{result['translated_text']}"
            else:
                response = result["message"]
            
            # Отправляем результат пользователю
            await message.answer(response)
            
        finally:
            db.close()