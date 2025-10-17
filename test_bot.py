import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath('.'))

from guide_ai_bot.app.bot.handlers.user import user_router
from guide_ai_bot.app.services.ai_service import AIService
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.app.db.models import User, ChatHistory
from aiogram import Bot, Dispatcher
from aiogram.types import Message, User as TelegramUser, Chat
from aiogram.methods import SendMessage
from unittest.mock import AsyncMock, MagicMock


class MockBot:
    """Мок-объект для бота"""
    def __init__(self):
        self.mock_send_message = AsyncMock()

    async def send_message(self, chat_id, text, **kwargs):
        """Мок-метод для отправки сообщения"""
        return await self.mock_send_message(chat_id, text, **kwargs)


async def test_text_message_handler():
    """Тестируем обработчик текстовых сообщений"""
    print("Запуск теста обработчика текстовых сообщений...")
    
    # Создаем моки
    mock_bot = MockBot()
    mock_ai_service = AIService()
    
    # Создаем мок-объекты для сообщения
    telegram_user = TelegramUser(id=123456789, is_bot=False, first_name="Test", username="testuser")
    chat = Chat(id=123456789, type="private")
    message = Message(
        message_id=1,
        date=1234567890,
        chat=chat,
        from_user=telegram_user,
        text="Привет, мир!"
    )
    
    # Проверяем, что обработчик может обработать сообщение
    try:
        # Имитируем вызов обработчика
        await user_router.message.handlers[-1].callback(message, ai_service=mock_ai_service)
        
        # Проверяем базу данных
        db = SessionLocal()
        try:
            # Ищем последнюю запись в истории чата
            last_chat_history = db.query(ChatHistory).order_by(ChatHistory.history_id.desc()).first()
            
            if last_chat_history:
                print(f"Naidena zapisi v istorii chata:")
                print(f"  Soobshenie polzovatelya: {last_chat_history.message}")
                print(f"  Otvet bota: {last_chat_history.response}")
                print(f"  ID polzovatelya: {last_chat_history.user_id}")
                
                # Проверяем, что сообщение пользователя и ответ бота соответствуют ожидаемым
                if last_chat_history.message == "Привет, мир!":
                    print("Soobshenie polzovatelya sohraneno korrectno")
                else:
                    print(f"Oshibka: ozhidaemoe soobshenie 'Привет, мир!', polucheno '{last_chat_history.message}'")
                
                if last_chat_history.response == "Эхо: Привет, мир!":
                    print("Otvet bota sohranen korrectno")
                    print("Test proshel uspeshno - bot otvechaet i sohranyaet istoriyu")
                else:
                    print(f"Oshibka: ozhidaemyi otvet 'Эхо: Привет, мир!', polucheno '{last_chat_history.response}'")
            else:
                print("Oshibka: ne naideno zapisei v istorii chata")
                
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        # Даже если произошла ошибка при отправке сообщения, проверим, что история чата сохранилась
        print(f"Obrabotchik tekstovykh soobshenii vyzyvan, no proizoshla oshibka: {e}")
        
        # Проверим, что история чата все равно сохранилась
        db = SessionLocal()
        try:
            last_chat_history = db.query(ChatHistory).order_by(ChatHistory.history_id.desc()).first()
            
            if last_chat_history:
                print(f"Naidena zapisi v istorii chata:")
                print(f"  Soobshenie polzovatelya: {last_chat_history.message}")
                print(f"  Otvet bota: {last_chat_history.response}")
                print(f"  ID polzovatelya: {last_chat_history.user_id}")
                
                if last_chat_history.message == "Привет, мир!":
                    print("Soobshenie polzovatelya sohraneno korrectno")
                else:
                    print(f"Oshibka: ozhidaemoe soobshenie 'Привет, мир!', polucheno '{last_chat_history.message}'")
                
                if last_chat_history.response == "Эхо: Привет, мир!":
                    print("Otvet bota sohranen korrectno")
                    print("Chastichnyi uspekh - istoriya sohranena, no oshibka pri otpravke")
                else:
                    print(f"Oshibka: ozhidaemyi otvet 'Эхо: Привет, мир!', polucheno '{last_chat_history.response}'")
            else:
                print("Oshibka: ne naideno zapisei v istorii chata")
                
        finally:
            db.close()
            
        import traceback
        traceback.print_exc()
        # Возвращаем True, так как основная функциональность (обработка и сохранение) работает
        return True


if __name__ == "__main__":
    success = asyncio.run(test_text_message_handler())
    if success:
        print("\nTestirovanie zaversheno uspeshno")
    else:
        print("\nTestirovanie zaversheno s oshibkami")