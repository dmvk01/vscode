from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.orm import sessionmaker
import random
from typing import Dict, Any

from guide_ai_bot.app.bot.modules.base_module import BaseModule
from guide_ai_bot.app.db.models import User, ChatHistory
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.app.services.ai_service import AIService
from guide_ai_bot.utils.logger import get_logger


class QuizModule(BaseModule):
    """
    Модуль викторины на основе ИИ
    """
    
    def __init__(self):
        super().__init__("quiz", "Викторина на основе ИИ")
        self.questions = [
            "Какой самый большой океан на Земле?",
            "Кто написал 'Войну и мир'?",
            "Какая столица Франции?",
            "Сколько планет в Солнечной системе?",
            "Кто создал компанию Apple?"
        ]
        self.answers = [
            "Тихий океан",
            "Лев Толстой",
            "Париж",
            "8",
            "Стив Джобс"
        ]
        self.logger = get_logger(__name__)
    
    def _setup_handlers(self):
        """
        Настраивает обработчики команд и сообщений модуля
        """
        @self.router.message(Command("quiz"))
        async def quiz_command_handler(message: types.Message):
            await self._start_quiz(message)
    
    async def _start_quiz(self, message: types.Message):
        """
        Запускает викторину для пользователя
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
            
            # Устанавливаем текущий модуль как 'quiz'
            user.current_module = 'quiz'
            db.commit()
            
            # Начинаем викторину
            await self._ask_question(user_id, message, db)
            
        finally:
            # Закрываем сессию
            db.close()
    
    async def _ask_question(self, user_id: int, message: types.Message, db: sessionmaker):
        """
        Задает случайный вопрос пользователю
        """
        # Выбираем случайный вопрос
        question_idx = random.randint(0, len(self.questions) - 1)
        question = self.questions[question_idx]
        
        # Сохраняем индекс вопроса в базе данных или в сессии
        # Для простоты сохраним в чат-истории как системное сообщение
        chat_history = ChatHistory(
            user_id=user_id,
            message=f"QUIZ_QUESTION_IDX:{question_idx}",
            response="",
            is_system=True  # Добавим поле is_system для обозначения системных сообщений
        )
        db.add(chat_history)
        db.commit()
        
        await message.answer(f"Викторина! 🧠\n\nВопрос: {question}\n\nВведите свой ответ:")
    
    async def execute(self, user_id: int, db: sessionmaker, user_message: str = None, **kwargs) -> Dict[str, Any]:
        """
        Обработка сообщений в модуле викторины
        """
        try:
            # Получаем последний вопрос из истории
            last_quiz_msg = db.query(ChatHistory).filter(
                ChatHistory.user_id == user_id,
                ChatHistory.message.like("QUIZ_QUESTION_IDX:%")
            ).order_by(ChatHistory.timestamp.desc()).first()
            
            if not last_quiz_msg:
                return {"status": "error", "message": "Не найден активный вопрос викторины"}
            
            # Извлекаем индекс вопроса
            question_idx = int(last_quiz_msg.message.split(":")[1])
            correct_answer = self.answers[question_idx]
            
            # Проверяем ответ пользователя
            user_answer = user_message.lower().strip() if user_answer else ""
            correct_answer_lower = correct_answer.lower().strip()
            
            is_correct = correct_answer_lower in user_answer or user_answer in correct_answer_lower
            
            result = {
                "status": "success",
                "is_correct": is_correct,
                "correct_answer": correct_answer,
                "user_answer": user_message
            }
            
            if is_correct:
                self.logger.info(f"Пользователь {user_id} правильно ответил на вопрос викторины", extra={'user_id': user_id})
                result["message"] = f"Правильно! 🎉 Ответ: {correct_answer}"
            else:
                self.logger.info(f"Пользователь {user_id} неправильно ответил на вопрос викторины", extra={'user_id': user_id})
                result["message"] = f"Неправильно. Правильный ответ: {correct_answer}\nВаш ответ: {user_message}"
            
            # Завершаем модуль викторины
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                user.current_module = 'chat'
                db.commit()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка в модуле викторины: {str(e)}", extra={'user_id': user_id, 'error_type': type(e).__name__})
            return {"status": "error", "message": f"Ошибка при обработке викторины: {str(e)}"}
    
    async def continue_quiz(self, message: types.Message, ai_service: AIService):
        """
        Продолжение обработки ответа пользователя на вопрос викторины
        """
        user_id = message.from_user.id
        user_answer = message.text
        
        db: sessionmaker = SessionLocal()
        
        try:
            # Проверяем, что пользователь находится в модуле викторины
            user = db.query(User).filter(User.user_id == user_id).first()
            
            if user.current_module != 'quiz':
                return
            
            # Выполняем модуль викторины с ответом пользователя
            result = await self.execute(user_id, db, user_message=user_answer)
            
            # Отправляем результат пользователю
            await message.answer(result["message"])
            
        finally:
            db.close()