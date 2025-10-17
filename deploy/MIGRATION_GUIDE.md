# Руководство по переносу Guide_AI_Bot

Это руководство описывает процесс переноса проекта Guide_AI_Bot с текущей среды разработки на сервер под управлением Debian 12 с Apache.

## Содержание

1. [Подготовка к переносу](#подготовка-к-переносу)
2. [Перенос файлов проекта](#перенос-файлов-проекта)
3. [Настройка сервера](#настройка-сервера)
4. [Запуск проекта](#запуск-проекта)
5. [Настройка Apache](#настройка-apache)
6. [Настройка systemd-сервисов](#настройка-systemd-сервисов)
7. [Проверка работы](#проверка-работы)
8. [Дополнительные настройки](#дополнительные-настройки)

## Подготовка к переносу

Перед началом переноса убедитесь, что:

1. У вас есть доступ к серверу под управлением Debian 12
2. У вас есть права sudo на сервере
3. У вас установлен Git на локальной машине
4. У вас есть SSH-доступ к серверу
5. У вас есть все необходимые API-ключи и учетные данные

## Перенос файлов проекта

### 1. Клонирование репозитория

На сервере выполните следующие команды:

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Git
sudo apt install git -y

# Клонируем репозиторий
git clone https://github.com/ваш_репозиторий/guide_ai_bot.git
cd guide_ai_bot
```

### 2. Перенос конфигурационных файлов

Скопируйте ваши локальные конфигурационные файлы на сервер:

```bash
# Скопируйте .env файл с вашими API-ключами
scp .env user@your_server_ip:/path/to/guide_ai_bot/.env

# Скопируйте любые другие конфигурационные файлы, если они есть
scp -r config/* user@your_server_ip:/path/to/guide_ai_bot/config/
```

## Настройка сервера

### 1. Установка зависимостей

```bash
# Перейдите в директорию проекта
cd /path/to/guide_ai_bot

# Сделайте скрипты исполняемыми
chmod +x deploy/*.sh

# Запустите скрипт установки зависимостей
sudo ./deploy/install_dependencies.sh
```

### 2. Настройка окружения

```bash
# Запустите скрипт настройки окружения
./deploy/setup_environment.sh
```

### 3. Инициализация базы данных

```bash
# Запустите скрипт инициализации базы данных
./deploy/setup_database.sh
```

## Запуск проекта

### 1. Активация виртуального окружения

```bash
# Активируйте виртуальное окружение
source venv/bin/activate
```

### 2. Проверка конфигурации

Убедитесь, что файл `.env` содержит все необходимые параметры:

```bash
# Откройте файл для редактирования
nano .env
```

Необходимые параметры:
- `BOT_TOKEN` - Токен вашего Telegram-бота
- `MISTRAL_API_KEY` - API-ключ Mistral AI
- `OPENROUTER_API_KEY` - API-ключ OpenRouter
- `ROBOKASSA_LOGIN` - Логин Robokassa
- `ROBOKASSA_PASSWORD1` - Пароль #1 Robokassa
- `ROBOKASSA_PASSWORD2` - Пароль #2 Robokassa
- `ROBOKASSA_TEST_MODE` - Режим тестирования Robokassa (true/false)
- `ADMIN_USERNAME` - Имя пользователя админ-панели
- `ADMIN_PASSWORD` - Пароль админ-панели

### 3. Тестовый запуск

```bash
# Запустите бота в режиме разработки
python -m guide_ai_bot.main

# В другом терминале запустите админ-панель
python run_admin.py

# В третьем терминале запустите веб-сервер (если используется вебхук)
python run_web.py
```

## Настройка Apache

### 1. Запуск скрипта настройки Apache

```bash
# Запустите скрипт настройки Apache
sudo ./deploy/configure_apache.sh
```

### 2. Настройка домена (опционально)

Если у вас есть домен, вы можете настроить его для доступа к админ-панели:

```bash
# Откройте конфигурационный файл Apache
sudo nano /etc/apache2/sites-available/guide_ai_bot.conf

# Измените ServerName на ваш домен:
# ServerName your_domain.com
# ServerAlias www.your_domain.com

# Перезапустите Apache
sudo systemctl restart apache2
```

## Настройка systemd-сервисов

### 1. Запуск скрипта развертывания

```bash
# Запустите основной скрипт развертывания
sudo ./deploy/deploy.sh
```

### 2. Проверка статуса сервисов

```bash
# Проверьте статус сервисов
sudo systemctl status guide_ai_bot.service
sudo systemctl status guide_ai_bot_admin.service
sudo systemctl status guide_ai_bot_web.service
```

### 3. Управление сервисами

```bash
# Запуск сервисов
sudo systemctl start guide_ai_bot.service
sudo systemctl start guide_ai_bot_admin.service
sudo systemctl start guide_ai_bot_web.service

# Остановка сервисов
sudo systemctl stop guide_ai_bot.service
sudo systemctl stop guide_ai_bot_admin.service
sudo systemctl stop guide_ai_bot_web.service

# Перезапуск сервисов
sudo systemctl restart guide_ai_bot.service
sudo systemctl restart guide_ai_bot_admin.service
sudo systemctl restart guide_ai_bot_web.service

# Просмотр логов
sudo journalctl -u guide_ai_bot.service -f
sudo journalctl -u guide_ai_bot_admin.service -f
sudo journalctl -u guide_ai_bot_web.service -f
```

## Проверка работы

### 1. Проверка бота

1. Откройте Telegram
2. Найдите вашего бота по @username
3. Отправьте команду `/start`
4. Проверьте, что бот отвечает

### 2. Проверка админ-панели

1. Откройте браузер
2. Перейдите по адресу: `http://your_server_ip:5000/admin/login`
3. Введите учетные данные администратора
4. Проверьте, что админ-панель работает

### 3. Проверка вебхука Robokassa

1. Войдите в личный кабинет Robokassa
2. Перейдите в раздел "Уведомления"
3. Укажите URL вебхука: `http://your_server_ip:5000/webhook/robokassa`
4. Проверьте, что вебхук работает

## Дополнительные настройки

### 1. Настройка SSL-сертификата (рекомендуется)

Для production-среды рекомендуется настроить SSL-сертификат с помощью Let's Encrypt:

```bash
# Установите certbot
sudo apt install certbot python3-certbot-apache -y

# Получите SSL-сертификат
sudo certbot --apache -d your_domain.com

# Перезапустите Apache
sudo systemctl restart apache2
```

### 2. Настройка брандмауэра

```bash
# Установите ufw
sudo apt install ufw -y

# Разрешите SSH, HTTP и HTTPS
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Включите брандмауэр
sudo ufw enable
```

### 3. Настройка резервного копирования

Создайте скрипт для регулярного резервного копирования базы данных:

```bash
# Создайте скрипт резервного копирования
nano backup_db.sh

# Добавьте следующее содержимое:
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/path/to/guide_ai_bot/guide_ai_bot.db"
BACKUP_DIR="/path/to/backups"
mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/guide_ai_bot_$DATE.db

# Сделайте скрипт исполняемым
chmod +x backup_db.sh

# Добавьте задачу в cron для ежедневного резервного копирования
crontab -e
# Добавьте строку:
# 0 2 * * * /path/to/guide_ai_bot/backup_db.sh
```

### 4. Мониторинг и логирование

Логи сервисов доступны через journalctl:

```bash
# Просмотр логов бота
sudo journalctl -u guide_ai_bot.service -f

# Просмотр логов админ-панели
sudo journalctl -u guide_ai_bot_admin.service -f

# Просмотр логов веб-сервера
sudo journalctl -u guide_ai_bot_web.service -f
```

Также логи записываются в директорию `logs/` проекта.

## Устранение неполадок

### 1. Бот не запускается

Проверьте логи:
```bash
sudo journalctl -u guide_ai_bot.service -f
```

Убедитесь, что все API-ключи указаны правильно в файле `.env`.

### 2. Админ-панель недоступна

Проверьте статус сервиса:
```bash
sudo systemctl status guide_ai_bot_admin.service
```

Проверьте конфигурацию Apache:
```bash
sudo systemctl status apache2
sudo nano /etc/apache2/sites-available/guide_ai_bot.conf
```

### 3. Проблемы с базой данных

Проверьте, что файл базы данных существует и доступен:
```bash
ls -la guide_ai_bot.db
```

Попробуйте пересоздать базу данных:
```bash
./deploy/setup_database.sh
```

## Обновление проекта

Для обновления проекта до новой версии:

```bash
# Остановите сервисы
sudo systemctl stop guide_ai_bot.service
sudo systemctl stop guide_ai_bot_admin.service
sudo systemctl stop guide_ai_bot_web.service

# Обновите код из репозитория
git pull origin main

# Установите новые зависимости (если есть)
source venv/bin/activate
pip install -r requirements.txt

# Запустите миграции базы данных (если есть)
alembic upgrade head

# Перезапустите сервисы
sudo systemctl start guide_ai_bot.service
sudo systemctl start guide_ai_bot_admin.service
sudo systemctl start guide_ai_bot_web.service
```

Теперь ваш проект Guide_AI_Bot успешно перенесен на сервер под управлением Debian 12 с Apache и готов к работе в production-среде.