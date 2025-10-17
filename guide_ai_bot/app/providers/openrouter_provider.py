import aiohttp
from typing import Dict, Any
from .base import AIProvider
from guide_ai_bot.core.config import settings


class OpenRouterProvider(AIProvider):
    """
    Класс для взаимодействия с OpenRouter API.
    """

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model_name = settings.openrouter_model_name
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    async def get_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Асинхронный метод для получения ответа от OpenRouter AI.

        :param prompt: Входной текст для генерации ответа
        :param kwargs: Дополнительные параметры, специфичные для провайдера
        :return: Словарь с результатами
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Извлекаем текст ответа из JSON-ответа OpenRouter API
                        response_text = result['choices'][0]['message']['content']
                        return {
                            "response": response_text,
                            "status": "success"
                        }
                    else:
                        return {
                            "response": "",
                            "status": "error",
                            "error": f"OpenRouter API error: {response.status}"
                        }
        except aiohttp.ClientError as e:
            return {
                "response": "",
                "status": "error",
                "error": f"Network error when calling OpenRouter API: {str(e)}"
            }
        except Exception as e:
            return {
                "response": "",
                "status": "error",
                "error": f"Unexpected error when calling OpenRouter API: {str(e)}"
            }