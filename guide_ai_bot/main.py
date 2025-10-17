# Основной файл приложения Guide_AI_Bot
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.methods import SetMyCommands
from aiogram.types import BotCommand

from guide_ai_bot.core.config import settings
from guide_ai_bot.app.bot.handlers.user import user_router
from guide_ai_bot.app.bot.handlers.balance import balance_router
from guide_ai_bot.app.services.ai_service import AIService
from guide_ai_bot.app.bot.middlewares.rate_limiter import RateLimitMiddleware
from guide_ai_bot.utils.logger import setup_logger


async def main():
    # Настройка логирования
    logger = setup_logger("guide_ai_bot.main", logging.INFO if not settings.debug else logging.DEBUG)
    logger.info("Запуск Guide_AI_Bot")
    
    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создание экземпляра сервиса ИИ
    ai_service = AIService()
    
    # Загрузка и инициализация модулей
    from guide_ai_bot.app.bot.utils.module_loader import module_loader
    module_loader.load_default_modules()
    
    # Инициализация диспетчера
    dp = Dispatcher()
    
    # Передача экземпляров сервисов в диспетчер
    dp["ai_service"] = ai_service
    dp["module_loader"] = module_loader
    
    # Добавление middleware для ограничения частоты запросов
    dp.message.middleware(RateLimitMiddleware(max_requests=10, time_window=60))
    
    # Подключение роутеров
    dp.include_router(user_router)
    dp.include_router(balance_router)
    
    # Подключение роутеров модулей
    for module_name, router in module_loader.routers.items():
        dp.include_router(router)
        logger.info(f"Роутер модуля {module_name} подключен")
    
    # Установка команд меню
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="ai_chat", description="Чат с ИИ"),
        BotCommand(command="premium", description="Включить Premium"),
        BotCommand(command="free", description="Бесплатный режим"),
        BotCommand(command="back", description="Выйти из текущего модуля"),
        BotCommand(command="balance", description="Баланс и пополнение"),
        BotCommand(command="settings", description="Настройки"),
        BotCommand(command="quiz", description="Викторина на основе ИИ"),
        BotCommand(command="translate", description="Переводчик"),
        BotCommand(command="image_gen", description="Генерация изображений (premium)"),
        BotCommand(command="lang", description="Выбор языка"),
        BotCommand(command="referral", description="Реферальная программа"),
        BotCommand(command="horoscope", description="Продвинутый гороскоп"),
        BotCommand(command="battle", description="Батл агентов")
    ]
    await bot.set_my_commands(commands)
    
    # Удаление вебхука и запуск поллинга
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Запуск polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
