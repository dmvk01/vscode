#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для управления ботом Guide_AI_Bot
Позволяет запускать, останавливать и перезапускать все компоненты бота
"""

import os
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path

# Глобальные переменные для процессов
processes = []


def signal_handler(sig, frame):
    """Обработчик сигналов для корректной остановки всех процессов"""
    print('\nПолучен сигнал остановки. Останавливаю все процессы...')
    stop_all_processes()
    sys.exit(0)


def start_process(script_name, process_name):
    """Запускает процесс и добавляет его в список"""
    try:
        # Проверяем, существует ли файл скрипта
        script_path = Path(script_name)
        if not script_path.exists():
            print(f"Ошибка: Скрипт {script_name} не найден")
            return None
        
        # Запускаем процесс
        if script_name.endswith('.py'):
            process = subprocess.Popen([sys.executable, script_name], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
        else:
            # Для других типов файлов (например, .bat)
            process = subprocess.Popen([script_name], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
        
        processes.append((process, process_name))
        print(f"Запущен процесс: {process_name} (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"Ошибка при запуске {process_name}: {str(e)}")
        return None


def stop_all_processes():
    """Останавливает все запущенные процессы"""
    for process, name in processes:
        try:
            if process.poll() is None:  # Процесс еще работает
                print(f"Останавливаю процесс: {name} (PID: {process.pid})")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"Принудительно убиваю процесс: {name}")
                    process.kill()
        except Exception as e:
            print(f"Ошибка при остановке {name}: {str(e)}")
    
    # Очищаем список процессов
    processes.clear()


def start_bot(daemon=False):
    """Запускает все компоненты бота"""
    print("Запуск Guide_AI_Bot...")
    
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем админ-панель
    admin_process = start_process('run_admin.py', 'Admin Panel')
    if admin_process:
        time.sleep(3)  # Ждем запуск админ-панели
    
    # Запускаем основного бота
    bot_process = start_process('-m guide_ai_bot.main', 'Main Bot')
    if bot_process:
        time.sleep(3)  # Ждем запуск бота
    
    # Запускаем веб-сервер (если нужен для вебхуков)
    web_process = start_process('run_web.py', 'Web Server')
    
    if daemon:
        print("Бот запущен в режиме демона. Для остановки используйте Ctrl+C")
        try:
            # Бесконечный цикл для режима демона
            while True:
                time.sleep(1)
                # Проверяем, работают ли все процессы
                for process, name in processes:
                    if process.poll() is not None:
                        print(f"Процесс {name} завершился неожиданно!")
                        # Здесь можно добавить логику перезапуска
        except KeyboardInterrupt:
            print("\nПолучен сигнал остановки...")
    else:
        print("Все компоненты бота запущены!")
        print("Админ-панель: http://127.0.0.1:5000/admin")
        print("Для остановки всех процессов используйте Ctrl+C")


def stop_bot():
    """Останавливает все компоненты бота"""
    print("Остановка Guide_AI_Bot...")
    stop_all_processes()
    print("Все компоненты бота остановлены!")


def restart_bot():
    """Перезапускает все компоненты бота"""
    print("Перезапуск Guide_AI_Bot...")
    stop_bot()
    time.sleep(2)
    start_bot()


def status_bot():
    """Показывает статус всех компонентов бота"""
    print("Статус Guide_AI_Bot:")
    if not processes:
        print("Нет запущенных процессов")
        return
    
    for process, name in processes:
        if process.poll() is None:
            print(f"✓ {name}: запущен (PID: {process.pid})")
        else:
            print(f"✗ {name}: остановлен")


def main():
    parser = argparse.ArgumentParser(description='Управление ботом Guide_AI_Bot')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'], 
                       help='Действие для выполнения')
    parser.add_argument('--daemon', '-d', action='store_true', 
                       help='Запустить в режиме демона')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        start_bot(args.daemon)
    elif args.action == 'stop':
        stop_bot()
    elif args.action == 'restart':
        restart_bot()
    elif args.action == 'status':
        status_bot()


if __name__ == '__main__':
    main()