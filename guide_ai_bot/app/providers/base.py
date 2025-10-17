from abc import ABC, abstractmethod
from typing import Dict, Any


class AIProvider(ABC):
    """
    Абстрактный базовый класс для всех AI-провайдеров.
    Определяет общий интерфейс для взаимодействия с различными AI-моделями.
    """

    @abstractmethod
    async def get_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Асинхронный метод для получения ответа от ИИ.

        :param prompt: Входной текст для генерации ответа
        :param kwargs: Дополнительные параметры, специфичные для провайдера
        :return: Словарь с результатами (например, 'response', 'status', 'error')
        """
        pass