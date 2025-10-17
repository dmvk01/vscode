#!/bin/bash

# Основной скрипт развертывания Guide_AI_Bot на Debian/Ubuntu
# Использование: sudo ./deploy.sh

set -e  # Завершить выполнение при ошибке

# Проверяем, запущен ли скрипт с правами root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root (sudo)" 
   exit 1
fi

# Определяем директорию проекта
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Начинаем развертывание Guide_AI_Bot в директории: $PROJECT_DIR"
echo ""

# 1. Установка зависимостей
echo "Шаг 1: Установка зависимостей..."
chmod +x "$PROJECT_DIR/deploy/install_dependencies.sh"
"$PROJECT_DIR/deploy/install_dependencies.sh"
echo "Шаг 1 завершен!"
echo ""

# 2. Настройка окружения
echo "Шаг 2: Настройка окружения..."
chmod +x "$PROJECT_DIR/deploy/setup_environment.sh"
sudo -u $SUDO_USER "$PROJECT_DIR/deploy/setup_environment.sh"
echo "Шаг 2 завершен!"
echo ""

# 3. Инициализация базы данных
echo "Шаг 3: Инициализация базы данных..."
chmod +x "$PROJECT_DIR/deploy/setup_database.sh"
sudo -u $SUDO_USER "$PROJECT_DIR/deploy/setup_database.sh"
echo "Шаг 3 завершен!"
echo ""

# 4. Настройка Apache
echo "Шаг 4: Настройка Apache..."
chmod +x "$PROJECT_DIR/deploy/configure_apache.sh"
"$PROJECT_DIR/deploy/configure_apache.sh"
echo "Шаг 4 завершен!"
echo ""

# 5. Создание systemd-сервиса для бота
echo "Шаг 5: Создание systemd-сервиса для бота..."
cat > /etc/systemd/system/guide_ai_bot.service << EOF
[Unit]
Description=Guide_AI_Bot Telegram Bot
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python -m guide_ai_bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd и включаем сервис
systemctl daemon-reload
systemctl enable guide_ai_bot.service
echo "Systemd-сервис для бота создан и включен!"
echo ""

# 6. Создание systemd-сервиса для админ-панели
echo "Шаг 6: Создание systemd-сервиса для админ-панели..."
cat > /etc/systemd/system/guide_ai_bot_admin.service << EOF
[Unit]
Description=Guide_AI_Bot Admin Panel
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python run_admin.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd и включаем сервис
systemctl daemon-reload
systemctl enable guide_ai_bot_admin.service
echo "Systemd-сервис для админ-панели создан и включен!"
echo ""

# 7. Создание systemd-сервиса для веб-сервера
echo "Шаг 7: Создание systemd-сервиса для веб-сервера..."
cat > /etc/systemd/system/guide_ai_bot_web.service << EOF
[Unit]
Description=Guide_AI_Bot Web Server
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python run_web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd и включаем сервис
systemctl daemon-reload
systemctl enable guide_ai_bot_web.service
echo "Systemd-сервис для веб-сервера создан и включен!"
echo ""

# 8. Настройка логирования
echo "Шаг 8: Настройка логирования..."
# Создаем директорию для логов, если она не существует
if [ ! -d /var/log/guide_ai_bot ]; then
    mkdir -p /var/log/guide_ai_bot
    chown $SUDO_USER:$SUDO_USER /var/log/guide_ai_bot
fi

# Настраиваем ротацию логов
cat > /etc/logrotate.d/guide_ai_bot << EOF
/var/log/guide_ai_bot/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $SUDO_USER
}
EOF
echo "Логирование настроено!"
echo ""

# 9. Запуск сервисов
echo "Шаг 9: Запуск сервисов..."
systemctl start guide_ai_bot.service
systemctl start guide_ai_bot_admin.service
systemctl start guide_ai_bot_web.service

echo "Сервисы запущены!"
echo ""

# 10. Вывод информации о развертывании
echo "Развертывание завершено!"
echo ""
echo "Информация о сервисах:"
echo "- Бот: systemctl status guide_ai_bot.service"
echo "- Админ-панель: systemctl status guide_ai_bot_admin.service"
echo "- Веб-сервер: systemctl status guide_ai_bot_web.service"
echo ""
echo "Логи сервисов:"
echo "- Бот: journalctl -u guide_ai_bot.service -f"
echo "- Админ-панель: journalctl -u guide_ai_bot_admin.service -f"
echo "- Веб-сервер: journalctl -u guide_ai_bot_web.service -f"
echo ""
echo "Админ-панель доступна по адресу:"
echo "- http://ваш_IP:5000/admin/login"
echo "- Логин по умолчанию: admin"
echo "- Пароль по умолчанию: admin123"
echo ""
echo "Пожалуйста, измените учетные данные администратора после первого входа!"
echo ""
echo "Также не забудьте настроить файл .env с вашими API-ключами:"
echo "nano $PROJECT_DIR/.env"