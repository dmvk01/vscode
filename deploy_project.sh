#!/bin/bash

# Скрипт для развертывания проекта Guide_AI_Bot на VPS

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install python3 python3-pip python3-venv sqlite3 libsqlite3-dev build-essential git -y

# Создание директории проекта (если не существует)
mkdir -p ~/guide_ai_bot_project
cd ~/guide_ai_bot_project

# Копирование файлов проекта (предполагается, что файлы уже скопированы)
# Если проект еще не скопирован, раскомментируйте следующую строку:
# git clone https://ваш_репозиторий.git .

# Создание и активация виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# Создание файла .env (замените значения на реальные)
cat > .env << EOF
# Переменные окружения для Guide_AI_Bot
BOT_TOKEN=ваш_токен_бота_здесь
DATABASE_URL=sqlite:///./guide_ai_bot.db
DEBUG=False
# AI Model Configuration
MISTRAL_API_KEY=ваш_mistral_api_key
MISTRAL_MODEL_NAME=mistral-small-latest
OPENROUTER_API_KEY=ваш_openrouter_api_key
OPENROUTER_MODEL_NAME=openchat/openchat-7b
AI_API_KEY=ваш_api_key
# Robokassa Configuration
ROBOKASSA_LOGIN=ваш_логин
ROBOKASSA_PASSWORD1=ваш_пароль1
ROBOKASSA_PASSWORD2=ваш_пароль2
ROBOKASSA_TEST_MODE=true
# Admin Panel Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
EOF

# Установка дополнительных пакетов для работы с базой данных
pip install aiosqlite

# Создание базы данных с помощью Alembic
alembic upgrade head

echo "Развертывание завершено!"
echo "Теперь вы можете запустить приложение с помощью команд:"
echo "source venv/bin/activate"
echo "python run.py"