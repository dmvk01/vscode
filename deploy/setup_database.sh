#!/bin/bash

# Скрипт для инициализации базы данных Guide_AI_Bot
# Использование: ./setup_database.sh

set -e  # Завершить выполнение при ошибке

# Определяем директорию проекта
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Инициализация базы данных в директории: $PROJECT_DIR"

# Активируем виртуальное окружение
echo "Активируем виртуальное окружение..."
source venv/bin/activate

# Проверяем, существует ли файл базы данных
if [ ! -f guide_ai_bot.db ]; then
    echo "Создаем файл базы данных..."
    touch guide_ai_bot.db
else
    echo "Файл базы данных уже существует"
fi

# Запускаем миграции Alembic
echo "Запускаем миграции базы данных..."
alembic upgrade head

echo "Инициализация базы данных завершена!"
echo ""
echo "Структура базы данных:"
echo "- users: Таблица пользователей"
echo "- chat_history: История чата"
echo "- transactions: Транзакции"
echo "- modules: Модули"
echo "- user_modules: Связь пользователей и модулей"
echo "- user_balance: Баланс пользователей"
echo "- settings: Настройки приложения"