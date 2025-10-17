import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from guide_ai_bot.app.providers.openrouter_provider import OpenRouterProvider

async def test_openrouter_provider():
    print("Тестируем OpenRouterProvider...")
    
    # Создаем экземпляр провайдера
    provider = OpenRouterProvider()
    
    # Проверяем, что переменные окружения загружены
    if not provider.api_key or provider.api_key == "your_openrouter_api_key":
        print("ПРЕДУПРЕЖДЕНИЕ: OPENROUTER_API_KEY не установлен или использует значение по умолчанию из .env.example")
        print("Для реального теста необходимо установить действительный API-ключ в .env файле")
        return
    
    prompt = "Привет, это тестовое сообщение для OpenRouter модели"
    
    print(f"Отправляем запрос к OpenRouter API: {prompt}")
    print(f"Модель: {provider.model_name}")
    
    response = await provider.get_response(prompt)
    
    print(f"Получен ответ: {response}")
    
    if response["status"] == "success":
        print("Тест OpenRouterProvider: УСПЕШНО")
    else:
        print(f"Тест OpenRouterProvider: ОШИБКА - {response['error']}")

if __name__ == "__main__":
    asyncio.run(test_openrouter_provider())