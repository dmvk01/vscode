#!/bin/bash

# Скрипт для настройки Apache в качестве веб-сервера для Guide_AI_Bot
# Использование: sudo ./configure_apache.sh

set -e  # Завершить выполнение при ошибке

# Проверяем, запущен ли скрипт с правами root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root (sudo)" 
   exit 1
fi

# Определяем директорию проекта
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Настройка Apache для проекта в директории: $PROJECT_DIR"

# Создаем конфигурационный файл Apache
echo "Создаем конфигурационный файл Apache..."
cat > /etc/apache2/sites-available/guide_ai_bot.conf << EOF
<VirtualHost *:80>
    ServerName guide_ai_bot.local
    DocumentRoot $PROJECT_DIR
    
    # Настройки WSGI для Flask-приложения (админ-панель)
    WSGIDaemonProcess guide_ai_bot python-path=$PROJECT_DIR python-home=$PROJECT_DIR/venv
    WSGIProcessGroup guide_ai_bot
    WSGIScriptAlias /admin $PROJECT_DIR/run_admin.py
    
    # Настройки WSGI для вебхуков
    WSGIDaemonProcess guide_ai_bot_webhooks python-path=$PROJECT_DIR python-home=$PROJECT_DIR/venv
    WSGIProcessGroup guide_ai_bot_webhooks
    WSGIScriptAlias /webhook $PROJECT_DIR/run_web.py
    
    # Разрешаем доступ к директории проекта
    <Directory $PROJECT_DIR>
        Require all granted
    </Directory>
    
    # Разрешаем доступ к run_admin.py
    <Directory $PROJECT_DIR>
        <Files run_admin.py>
            Require all granted
        </Files>
    </Directory>
    
    # Разрешаем доступ к run_web.py
    <Directory $PROJECT_DIR>
        <Files run_web.py>
            Require all granted
        </Files>
    </Directory>
    
    # Логи Apache
    ErrorLog \${APACHE_LOG_DIR}/guide_ai_bot_error.log
    CustomLog \${APACHE_LOG_DIR}/guide_ai_bot_access.log combined
    
    # Проксирование запросов к боту (если используется вебхук)
    ProxyPreserveHost On
    ProxyPass /webhook/robokassa http://127.0.0.1:5000/webhook/robokassa
    ProxyPassReverse /webhook/robokassa http://127.0.0.1:5000/webhook/robokassa
</VirtualHost>
EOF

# Включаем сайт
echo "Включаем сайт..."
a2ensite guide_ai_bot.conf

# Перезапускаем Apache
echo "Перезапускаем Apache..."
systemctl restart apache2

echo "Настройка Apache завершена!"
echo ""
echo "Теперь вы можете получить доступ к админ-панели по адресу:"
echo "http://guide_ai_bot.local/admin"
echo ""
echo "Для получения доступа извне, добавьте запись в /etc/hosts:"
echo "sudo echo '127.0.0.1 guide_ai_bot.local' >> /etc/hosts"
echo ""
echo "Или замените ServerName в конфигурации на ваш внешний IP или домен."