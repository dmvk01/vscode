from typing import List, Dict, Optional
from guide_ai_bot.app.db.models import User


class MenuBuilder:
    """Класс для формирования текстового меню в стиле BotFather"""
    
    def __init__(self):
        # Определяем доступные команды меню
        self.menu_commands = [
            {
                'command': '/ai_chat',
                'description': 'Чат с ИИ',
                'requires_premium': False
            },
            {
                'command': '/horoscope',
                'description': 'Продвинутый гороскоп',
                'requires_premium': False
            },
            {
                'command': '/battle',
                'description': 'Батл агентов',
                'requires_premium': False
            },
            {
                'command': '/balance',
                'description': 'Баланс и пополнение',
                'requires_premium': False
            },
            {
                'command': '/settings',
                'description': 'Настройки',
                'requires_premium': False
            },
            {
                'command': '/premium',
                'description': 'Включить Premium',
                'requires_premium': False
            },
            {
                'command': '/free',
                'description': 'Бесплатный режим',
                'requires_premium': False
            },
            {
                'command': '/quiz',
                'description': 'Викторина на основе ИИ',
                'requires_premium': False
            },
            {
                'command': '/translate',
                'description': 'Переводчик',
                'requires_premium': False
            },
            {
                'command': '/image_gen',
                'description': 'Генерация изображений (premium)',
                'requires_premium': True
            },
            {
                'command': '/lang',
                'description': 'Выбор языка',
                'requires_premium': False
            },
            {
                'command': '/referral',
                'description': 'Реферальная программа',
                'requires_premium': False
            },
            {
                'command': '/back',
                'description': 'Выйти из текущего модуля (если активен)',
                'requires_premium': False
            }
        ]
    
    def build_menu(self, user: User) -> str:
        """
        Формирует текстовое меню для пользователя
        
        Args:
            user: Объект пользователя из базы данных
            
        Returns:
            Строку с текстовым меню
        """
        # Определяем текущий режим пользователя
        mode_emoji = "🟢" if user.subscription_type == "Free" else "🟣"
        mode_text = "Free" if user.subscription_type == "Free" else "Premium"
        
        # Формируем заголовок меню
        menu_text = f"🤖 Guide_AI_Bot — главное меню\n"
        menu_text += f"Текущий режим: {mode_emoji} {mode_text}\n\n"
        
        # Добавляем команды в меню
        for command_info in self.menu_commands:
            # Проверяем, доступна ли команда для текущего пользователя
            if command_info['requires_premium'] and user.subscription_type != "Premium":
                # Для команд, требующих премиум, добавляем пометку
                menu_text += f"{command_info['command']} — {command_info['description']} (premium)\n"
            else:
                menu_text += f"{command_info['command']} — {command_info['description']}\n"
        
        return menu_text
    
    def get_available_commands(self, user: User) -> List[str]:
        """
        Возвращает список доступных команд для пользователя
        
        Args:
            user: Объект пользователя из базы данных
            
        Returns:
            Список команд, доступных пользователю
        """
        available_commands = []
        
        for command_info in self.menu_commands:
            if command_info['requires_premium'] and user.subscription_type != "Premium":
                # Команда требует премиум, но пользователь не премиум
                continue
            else:
                available_commands.append(command_info['command'].replace('/', ''))
        
        return available_commands