#!/bin/bash

# Скрипт для настройки окружения проекта Guide_AI_Bot
# Использование: ./setup_environment.sh

set -e  # Завершить выполнение при ошибке

# Определяем директорию проекта
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Настройка окружения в директории: $PROJECT_DIR"

# Создаем виртуальное окружение
echo "Создаем виртуальное окружение..."
python3 -m venv venv

# Активируем виртуальное окружение
echo "Активируем виртуальное окружение..."
source venv/bin/activate

# Обновляем pip
echo "Обновляем pip..."
pip install --upgrade pip

# Устанавливаем зависимости из requirements.txt
echo "Устанавливаем зависимости из requirements.txt..."
pip install -r requirements.txt

# Создаем файл .env, если он не существует
if [ ! -f .env ]; then
    echo "Создаем файл .env из шаблона..."
    cp .env.example .env
    
    echo "Пожалуйста, отредактируйте файл .env и добавьте ваши API-ключи:"
    echo "nano .env"
fi

# Создаем директорию для логов, если она не существует
if [ ! -d logs ]; then
    echo "Создаем директорию для логов..."
    mkdir -p logs
fi

# Создаем директорию для временных файлов, если она не существует
if [ ! -d temp ]; then
    echo "Создаем директорию для временных файлов..."
    mkdir -p temp
fi

# Запускаем миграции базы данных
echo "Запускаем миграции базы данных..."
alembic upgrade head

echo "Настройка окружения завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте файл .env и добавьте ваши API-ключи:"
echo "   nano .env"
echo ""
echo "2. Запустите бота в режиме разработки:"
echo "   source venv/bin/activate"
echo "   python -m guide_ai_bot.main"
echo ""
echo "3. Для запуска админ-панели:"
echo "   source venv/bin/activate"
echo "   python run_admin.py"
echo ""
echo "4. Для запуска веб-сервера (если используется вебхук):"
echo "   source venv/bin/activate"
echo "   python run_web.py"