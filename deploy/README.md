# Скрипты развертывания Guide_AI_Bot на Debian

Эта директория содержит скрипты для автоматического развертывания Guide_AI_Bot на системах Debian/Ubuntu.

## Содержание

1. `install_dependencies.sh` - Установка всех необходимых зависимостей
2. `setup_environment.sh` - Настройка окружения и переменных
3. `configure_apache.sh` - Настройка Apache в качестве веб-сервера
4. `setup_database.sh` - Инициализация базы данных
5. `deploy.sh` - Основной скрипт развертывания

## Требования

- Debian 12 или Ubuntu 22.04+
- Доступ к root или sudo
- Интернет-соединение

## Использование

1. Склонируйте репозиторий:
   ```bash
   git clone https://github.com/ваш_репозиторий/guide_ai_bot.git
   cd guide_ai_bot
   ```

2. Сделайте скрипты исполняемыми (в Linux/macOS):
   ```bash
   chmod +x deploy/*.sh
   ```
   
   В Windows используйте PowerShell для запуска скриптов:
   ```powershell
   .\deploy\deploy.ps1
   ```
   Или запустите каждый скрипт по отдельности с помощью Python:
   ```cmd
   python deploy\install_dependencies.py
   python deploy\setup_environment.py
   python deploy\setup_database.py
   python deploy\configure_apache.py
   ```

3. Запустите основной скрипт развертывания:
   ```bash
   sudo ./deploy/deploy.sh
   ```
   
   В Windows запустите от имени администратора:
   ```cmd
   deploy\deploy.bat
   ```

## Конфигурация

После развертывания вам нужно будет настроить переменные окружения в файле `.env`:
- `BOT_TOKEN` - Токен вашего Telegram-бота
- `MISTRAL_API_KEY` - API-ключ Mistral AI
- `OPENROUTER_API_KEY` - API-ключ OpenRouter
- `ROBOKASSA_LOGIN` - Логин Robokassa
- `ROBOKASSA_PASSWORD1` - Пароль #1 Robokassa
- `ROBOKASSA_PASSWORD2` - Пароль #2 Robokassa

## Управление сервисом

После развертывания бот будет работать как systemd-сервис:
- `sudo systemctl start guide_ai_bot` - Запуск бота
- `sudo systemctl stop guide_ai_bot` - Остановка бота
- `sudo systemctl restart guide_ai_bot` - Перезапуск бота
- `sudo systemctl status guide_ai_bot` - Проверка статуса бота

Логи сервиса доступны через journalctl:
- `sudo journalctl -u guide_ai_bot -f` - Просмотр логов в реальном времени

## Админ-панель

Админ-панель будет доступна по адресу:
- `http://ваш_сервер:5000/admin/login`
- Логин по умолчанию: admin
- Пароль по умолчанию: admin123

Рекомендуется изменить учетные данные после первого входа.