import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from guide_ai_bot.app.providers.mistral_provider import MistralProvider

async def test_mistral_provider():
    print("Тестируем MistralProvider...")
    
    # Создаем экземпляр провайдера
    provider = MistralProvider()
    
    # Проверяем, что переменные окружения загружены
    if not provider.api_key or provider.api_key == "your_mistral_api_key":
        print("ПРЕДУПРЕЖДЕНИЕ: MISTRAL_API_KEY не установлен или использует значение по умолчанию из .env.example")
        print("Для реального теста необходимо установить действительный API-ключ в .env файле")
        return
    
    prompt = "Привет, это тестовое сообщение для Mistral модели"
    
    print(f"Отправляем запрос к Mistral API: {prompt}")
    print(f"Модель: {provider.model_name}")
    
    response = await provider.get_response(prompt)
    
    print(f"Получен ответ: {response}")
    
    if response["status"] == "success":
        print("Тест MistralProvider: УСПЕШНО")
    else:
        print(f"Тест MistralProvider: ОШИБКА - {response['error']}")

if __name__ == "__main__":
    asyncio.run(test_mistral_provider())