from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from guide_ai_bot.app.db.models import User, ChatHistory
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.app.services.ai_service import AIService
from guide_ai_bot.utils.menu_builder import MenuBuilder
from guide_ai_bot.utils.security import InputModerator
from guide_ai_bot.utils.speech_recognition import SpeechToText
from guide_ai_bot.utils.logger import get_logger


logger = get_logger(__name__)

# Создание роутера
user_router = Router()


@user_router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Обработчик команды /start
    Проверяет, есть ли пользователь в базе данных. Если нет — создает новую запись.
    Отправляет приветственное сообщение и запрашивает согласие на обработку данных.
    """
    # Получаем информацию о пользователе из сообщения
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Создаем сессию для работы с базой данных
    db: sessionmaker = SessionLocal()
    
    try:
        # Проверяем, существует ли пользователь в базе данных
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            # Если пользователя нет в базе, создаем новую запись
            user = User(
                user_id=user_id,
                username=username,
                consent=None  # Устанавливаем consent в NULL при первом запуске
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Проверяем, предоставлено ли согласие на обработку данных
        if user.consent is None:
            # Запрашиваем согласие у пользователя
            consent_message = (
                "🤖 Привет! Я Guide_AI_Bot.\n"
                "Ты можешь просто начать писать — я отвечу как ИИ.\n"
                "Чтобы увидеть все функции — открой меню:\n\n"
                "Для продолжения использования бота, пожалуйста, подтвердите согласие "
                "на обработку персональных данных."
            )
            
            # Создаем inline-кнопки только для согласия
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Согласен", callback_data="consent_given"),
                    InlineKeyboardButton(text="Не согласен", callback_data="consent_denied")
                ]
            ])
            
            await message.answer(consent_message, reply_markup=keyboard)
        else:
            # Если согласие уже предоставлено, отправляем меню
            menu_builder = MenuBuilder()
            menu_text = menu_builder.build_menu(user)
            await message.answer(menu_text)
    
    finally:
        # Закрываем сессию
        db.close()


@user_router.message(Command("menu"))
async def menu_handler(message: types.Message):
    """
    Обработчик команды /menu
    Отправляет пользователю текстовое меню в стиле BotFather
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
                "Для доступа к меню, пожалуйста, подтвердите согласие "
                "на обработку персональных данных с помощью команды /start."
            )
            await message.answer(consent_message)
            return

        # Формируем и отправляем меню
        menu_builder = MenuBuilder()
        menu_text = menu_builder.build_menu(user)
        await message.answer(menu_text)

    finally:
        # Закрываем сессию
        db.close()


@user_router.message(Command("back"))
async def back_handler(message: types.Message):
    """
    Обработчик команды /back
    Позволяет пользователю выйти из текущего модуля и вернуться в основной чат
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
                "Для использования этой команды, пожалуйста, подтвердите согласие "
                "на обработку персональных данных с помощью команды /start."
            )
            await message.answer(consent_message)
            return

        # Проверяем, находится ли пользователь в каком-либо модуле
        if user.current_module is None or user.current_module == 'chat':
            await message.answer("Вы уже в основном чате.")
        else:
            # Сбрасываем текущий модуль и возвращаемся в основной чат
            previous_module = user.current_module
            user.current_module = 'chat'
            db.commit()
            await message.answer(f"Вы вышли из модуля '{previous_module}' и вернулись в основной чат.")

    finally:
        # Закрываем сессию
        db.close()


@user_router.message(Command("ai_chat"))
async def ai_chat_handler(message: types.Message):
    """
    Обработчик команды /ai_chat
    Переключает пользователя в режим чата с ИИ
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
                "Для использования этой команды, пожалуйста, подтвердите согласие "
                "на обработку персональных данных с помощью команды /start."
            )
            await message.answer(consent_message)
            return

        # Устанавливаем текущий модуль как 'chat'
        user.current_module = 'chat'
        db.commit()
        await message.answer("Вы перешли в режим чата с ИИ.")

    finally:
        # Закрываем сессию
        db.close()


@user_router.message(Command("premium"))
async def premium_handler(message: types.Message):
    """
    Обработчик команды /premium
    Переключает пользователя в премиум режим
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
                "Для использования этой команды, пожалуйста, подтвердите согласие "
                "на обработку персональных данных с помощью команды /start."
            )
            await message.answer(consent_message)
            return

        # Устанавливаем премиум режим
        user.subscription_type = 'Premium'
        db.commit()
        await message.answer("Режим Premium активирован.")

    finally:
        # Закрываем сессию
        db.close()


@user_router.message(Command("free"))
async def free_handler(message: types.Message):
    """
    Обработчик команды /free
    Переключает пользователя в бесплатный режим
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
                "Для использования этой команды, пожалуйста, подтвердите согласие "
                "на обработку персональных данных с помощью команды /start."
            )
            await message.answer(consent_message)
            return

        # Устанавливаем бесплатный режим
        user.subscription_type = 'Free'
        db.commit()
        await message.answer("Бесплатный режим активирован.")

    finally:
        # Закрываем сессию
        db.close()


@user_router.message(lambda message: message.content_type == ContentType.TEXT)
async def handle_text_message(message: types.Message, ai_service: AIService):
    """
    Обработчик текстовых сообщений.
    Отправляет сообщение в ИИ, сохраняет в историю и возвращает ответ пользователю.
    """
    user_id = message.from_user.id
    user_message = message.text

    # Получаем сессию для работы с базой данных
    db: sessionmaker = SessionLocal()

    try:
        # Получаем пользователя из базы данных
        user = db.query(User).filter(User.user_id == user_id).first()
        
        # Проверяем, предоставлено ли согласие на обработку данных
        if user.consent is None or user.consent is False:
            # Если согласие не предоставлено, отправляем запрос на согласие
            consent_message = (
                "Для продолжения использования бота, пожалуйста, подтвердите согласие "
                "на обработку персональных данных с помощью команды /start."
            )
            await message.answer(consent_message)
            return

        # Проверяем, есть ли активный модуль у пользователя
        if user.current_module and user.current_module != 'chat':
            # Если активен не основной чат, направляем сообщение в соответствующий модуль
            if user.current_module == 'quiz':
                # Импортируем модуль викторины для обработки ответа
                from guide_ai_bot.app.bot.modules.quiz_module import QuizModule
                quiz_module = QuizModule()
                await quiz_module.continue_quiz(message, ai_service)
            elif user.current_module == 'translate':
                # Импортируем модуль перевода для обработки текста
                from guide_ai_bot.app.bot.modules.translate_module import TranslateModule
                translate_module = TranslateModule()
                await translate_module.continue_translation(message, ai_service)
            else:
                # В реальной реализации здесь будет логика перенаправления в другие активные модули
                module_message = f"Сообщение отправлено в активный модуль: {user.current_module}"
                await message.answer(module_message)
        else:
            # Модерируем ввод пользователя
            moderator = InputModerator()
            is_safe, error_message = moderator.moderate_input(user_message)
            
            if not is_safe:
                await message.answer(error_message)
                return

            # Если активен основной чат или нет активного модуля, обрабатываем как обычно
            # Получаем ответ от ИИ
            ai_response = await ai_service.get_response(user_message, user_id)

            # Сохраняем сообщение и ответ в историю чата
            chat_history = ChatHistory(
                user_id=user_id,
                message=user_message,
                response=ai_response
            )
            db.add(chat_history)
            db.commit()

            # Отправляем ответ пользователю
            await message.answer(ai_response)

    finally:
        # Закрываем сессию
        db.close()


@user_router.callback_query(lambda c: c.data == "show_menu")
async def process_menu_callback(callback_query: types.CallbackQuery):
    """
    Обработчик inline-кнопки '📋 Меню'
    """
    user_id = callback_query.from_user.id

    # Создаем сессию для работы с базой данных
    db: sessionmaker = SessionLocal()

    try:
        # Получаем пользователя из базы данных
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            await callback_query.answer("Ошибка: Пользователь не найден", show_alert=True)
            return

        # Проверяем, предоставлено ли согласие на обработку данных
        if user.consent is None or user.consent is False:
            consent_message = (
                "Для доступа к меню, пожалуйста, подтвердите согласие "
                "на обработку персональных данных с помощью команды /start."
            )
            await callback_query.answer(consent_message, show_alert=True)
            return

        # Формируем и отправляем меню
        menu_builder = MenuBuilder()
        menu_text = menu_builder.build_menu(user)
        await callback_query.message.answer(menu_text)

        # Отвечаем на callback_query
        await callback_query.answer()

    finally:
        # Закрываем сессию
        db.close()


@user_router.callback_query(lambda c: c.data == "consent_given")
async def process_consent_given_callback(callback_query: types.CallbackQuery):
    """
    Обработчик inline-кнопки 'Согласен'
    """
    user_id = callback_query.from_user.id

    # Создаем сессию для работы с базой данных
    db: sessionmaker = SessionLocal()

    try:
        # Получаем пользователя из базы данных
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            await callback_query.answer("Ошибка: Пользователь не найден", show_alert=True)
            return

        # Устанавливаем согласие пользователя
        user.consent = True
        db.commit()

        # Отправляем меню
        menu_builder = MenuBuilder()
        menu_text = menu_builder.build_menu(user)
        await callback_query.message.answer(menu_text)

        # Отвечаем на callback_query
        await callback_query.answer("Спасибо за согласие! Теперь вы можете использовать все функции бота.")

    finally:
        # Закрываем сессию
        db.close()


@user_router.callback_query(lambda c: c.data == "consent_denied")
async def process_consent_denied_callback(callback_query: types.CallbackQuery):
    """
    Обработчик inline-кнопки 'Не согласен'
    """
    user_id = callback_query.from_user.id

    # Создаем сессию для работы с базой данных
    db: sessionmaker = SessionLocal()

    try:
        # Получаем пользователя из базы данных
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            await callback_query.answer("Ошибка: Пользователь не найден", show_alert=True)
            return

        # Устанавливаем отсутствие согласия пользователя
        user.consent = False
        db.commit()

        # Отправляем сообщение о ограничении функционала
        restricted_message = (
            "Без согласия на обработку данных вы можете использовать ограниченный функционал бота.\n"
            "Для полного доступа к функциям, пожалуйста, дайте согласие."
        )
        await callback_query.message.answer(restricted_message)

        # Отвечаем на callback_query
        await callback_query.answer("Вы не дали согласие на обработку данных. Функционал бота ограничен.")

    finally:
        # Закрываем сессию
        db.close()


@user_router.message(lambda message: message.content_type == ContentType.VOICE)
async def handle_voice_message(message: types.Message, ai_service: AIService):
    """
    Обработчик голосовых сообщений.
    Преобразует голос в текст, отправляет в ИИ, сохраняет в историю и возвращает ответ пользователю.
    """
    user_id = message.from_user.id

    logger.info(f"Получено голосовое сообщение от пользователя {user_id}", extra={'user_id': user_id})

    # Создаем сессию для работы с базой данных
    db: sessionmaker = SessionLocal()

    try:
        # Получаем пользователя из базы данных
        user = db.query(User).filter(User.user_id == user_id).first()
        
        # Проверяем, предоставлено ли согласие на обработку данных
        if user.consent is None or user.consent is False:
            # Если согласие не предоставлено, отправляем запрос на согласие
            consent_message = (
                "Для продолжения использования бота, пожалуйста, подтвердите согласие "
                "на обработку персональных данных с помощью команды /start."
            )
            await message.answer(consent_message)
            logger.warning(f"Пользователь {user_id} не дал согласия на обработку данных", extra={'user_id': user_id})
            return

        # Отправляем уведомление пользователю, что его голосовое сообщение обрабатывается
        processing_msg = await message.answer("Обрабатываю голосовое сообщение...")

        # Получаем информацию о голосовом файле
        voice_file_id = message.voice.file_id
        voice_file = await message.bot.get_file(voice_file_id)
        voice_file_path = voice_file.file_path

        # Скачиваем голосовой файл
        voice_file_binary = await message.bot.download_file(voice_file_path)
        
        # Создаем временный файл для сохранения голосового сообщения
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_voice_file:
            temp_voice_file.write(voice_file_binary.read())
            temp_voice_file_path = temp_voice_file.name

        try:
            # Используем SpeechToText для преобразования голоса в текст
            speech_recognizer = SpeechToText()
            user_message = await speech_recognizer.recognize_speech_from_telegram_voice(temp_voice_file_path)

            # Проверяем, успешно ли прошло распознавание
            if not user_message or "ошибка" in user_message.lower() or "не удалось" in user_message.lower():
                await message.answer(user_message or "Ошибка при распознавании голосового сообщения.")
                logger.error(f"Ошибка распознавания голоса от пользователя {user_id}: {user_message}", extra={'user_id': user_id})
                return

            logger.info(f"Голосовое сообщение от пользователя {user_id} распознано: {user_message[:50]}...", extra={'user_id': user_id})

            # Проверяем, есть ли активный модуль у пользователя
            if user.current_module and user.current_module != 'chat':
                # Если активен не основной чат, направляем сообщение в соответствующий модуль
                module_message = f"Сообщение отправлено в активный модуль: {user.current_module} (распознано из голоса: {user_message})"
                await message.answer(module_message)
                logger.info(f"Сообщение отправлено в модуль {user.current_module} для пользователя {user_id}", extra={'user_id': user_id, 'module': user.current_module})
            else:
                # Модерируем ввод пользователя
                moderator = InputModerator()
                is_safe, error_message = moderator.moderate_input(user_message)
                
                if not is_safe:
                    await message.answer(error_message)
                    logger.warning(f"Небезопасный контент от пользователя {user_id}: {user_message}", extra={'user_id': user_id})
                    return

                # Если активен основной чат или нет активного модуля, обрабатываем как обычно
                # Получаем ответ от ИИ
                ai_response = await ai_service.get_response(user_message, user_id)

                # Сохраняем сообщение (распознанный текст) и ответ в историю чата
                chat_history = ChatHistory(
                    user_id=user_id,
                    message=user_message,  # Сохраняем распознанный текст
                    response=ai_response
                )
                db.add(chat_history)
                db.commit()

                logger.info(f"Ответ на голосовое сообщение пользователя {user_id} сгенерирован успешно", extra={'user_id': user_id})

                # Отправляем ответ пользователю
                await message.answer(ai_response)

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_voice_file_path):
                os.unlink(temp_voice_file_path)
                logger.debug(f"Временный файл голосового сообщения удален для пользователя {user_id}", extra={'user_id': user_id})

    finally:
        # Закрываем сессию
        db.close()