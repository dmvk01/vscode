# Точка входа для запуска бота
from guide_ai_bot.main import main

if __name__ == "__main__":
    print("Запуск Guide_AI_Bot...")
    # Запуск основной функции бота
    import asyncio
    asyncio.run(main())
