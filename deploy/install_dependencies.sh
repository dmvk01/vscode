#!/bin/bash

# Скрипт для установки всех необходимых зависимостей на Debian/Ubuntu
# Использование: sudo ./install_dependencies.sh

set -e  # Завершить выполнение при ошибке

# Проверяем, запущен ли скрипт с правами root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root (sudo)" 
   exit 1
fi

echo "Начинаем установку зависимостей..."

# Обновляем список пакетов
echo "Обновляем список пакетов..."
apt update

# Устанавливаем основные зависимости
echo "Устанавливаем основные зависимости..."
apt install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip \
    nano \
    sqlite3 \
    apache2 \
    libapache2-mod-wsgi-py3 \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio

# Устанавливаем дополнительные зависимости для работы с аудио
echo "Устанавливаем дополнительные зависимости для работы с аудио..."
apt install -y \
    libsndfile1 \
    sox

# Включаем необходимые модули Apache
echo "Включаем необходимые модули Apache..."
a2enmod rewrite
a2enmod ssl
a2enmod headers
a2enmod proxy
a2enmod proxy_http
a2enmod proxy_wstunnel

# Перезапускаем Apache
echo "Перезапускаем Apache..."
systemctl restart apache2

echo "Установка зависимостей завершена!"
echo "Теперь можно запустить скрипт настройки окружения: ./setup_environment.sh"