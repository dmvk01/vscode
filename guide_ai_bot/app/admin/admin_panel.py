from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy.orm import sessionmaker
from guide_ai_bot.app.db.models import User, ChatHistory, Transaction, UserBalance
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.core.config import settings
from guide_ai_bot.utils.logger import get_logger
from datetime import datetime
import os


class AdminPanel:
    """
    Админ-панель для управления ботом
    """
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)  # Секретный ключ для сессий
        self.logger = get_logger(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """
        Настраивает маршруты админ-панели
        """
        from guide_ai_bot.app.db.settings_service import settings_service
        
        @self.app.route('/admin/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                
                # Простая проверка (в реальном приложении использовать хеширование паролей)
                if username == settings.admin_username and password == settings.admin_password:
                    session['logged_in'] = True
                    session['username'] = username
                    self.logger.info(f"Администратор {username} вошел в систему")
                    return redirect(url_for('admin_dashboard'))
                else:
                    return render_template('admin/login.html', error='Неверный логин или пароль')
            
            return render_template('admin/login.html')
        
        @self.app.route('/admin/logout')
        def logout():
            session.pop('logged_in', None)
            session.pop('username', None)
            self.logger.info("Администратор вышел из системы")
            return redirect(url_for('login'))
        
        @self.app.route('/admin/dashboard')
        def admin_dashboard():
            if not session.get('logged_in'):
                return redirect(url_for('login'))
            
            db: sessionmaker = SessionLocal()
            try:
                # Получаем общую статистику
                total_users = db.query(User).count()
                total_messages = db.query(ChatHistory).count()
                total_transactions = db.query(Transaction).count()
                
                # Получаем последние пользователи
                recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
                
                # Получаем последние транзакции
                recent_transactions = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(10).all()
                
                return render_template(
                    'admin/dashboard.html',
                    total_users=total_users,
                    total_messages=total_messages,
                    total_transactions=total_transactions,
                    recent_users=recent_users,
                    recent_transactions=recent_transactions
                )
            finally:
                db.close()
        
        @self.app.route('/admin/users')
        def admin_users():
            if not session.get('logged_in'):
                return redirect(url_for('login'))
            
            page = request.args.get('page', 1, type=int)
            per_page = 20
            offset = (page - 1) * per_page
            
            db: sessionmaker = SessionLocal()
            try:
                # Получаем пользователей с пагинацией
                users = db.query(User).offset(offset).limit(per_page).all()
                total_users = db.query(User).count()
                
                return render_template(
                    'admin/users.html',
                    users=users,
                    total_users=total_users,
                    current_page=page,
                    total_pages=(total_users + per_page - 1) // per_page
                )
            finally:
                db.close()
        
        @self.app.route('/admin/user/<int:user_id>')
        def admin_user_detail(user_id):
            if not session.get('logged_in'):
                return redirect(url_for('login'))
            
            db: sessionmaker = SessionLocal()
            try:
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return "Пользователь не найден", 404
                
                # Получаем историю чата пользователя
                chat_history = db.query(ChatHistory).filter(
                    ChatHistory.user_id == user_id
                ).order_by(ChatHistory.timestamp.desc()).limit(50).all()
                
                # Получаем транзакции пользователя
                transactions = db.query(Transaction).filter(
                    Transaction.user_id == user_id
                ).order_by(Transaction.created_at.desc()).limit(20).all()
                
                # Получаем баланс пользователя
                user_balance = db.query(UserBalance).filter(
                    UserBalance.user_id == user_id
                ).first()
                
                return render_template(
                    'admin/user_detail.html',
                    user=user,
                    chat_history=chat_history,
                    transactions=transactions,
                    user_balance=user_balance
                )
            finally:
                db.close()
        
        @self.app.route('/admin/settings/robokassa', methods=['GET', 'POST'])
        def admin_robokassa_settings():
            if not session.get('logged_in'):
                return redirect(url_for('login'))
            
            # Получаем настройки из базы данных
            settings_data = {
                'robokassa_login': settings_service.get_setting('robokassa_login', getattr(settings, 'robokassa_login', '')),
                'robokassa_password1': settings_service.get_setting('robokassa_password1', getattr(settings, 'robokassa_password1', '')),
                'robokassa_password2': settings_service.get_setting('robokassa_password2', getattr(settings, 'robokassa_password2', '')),
                'robokassa_test_mode': settings_service.get_setting('robokassa_test_mode', str(getattr(settings, 'robokassa_test_mode', True))).lower() in ['true', '1', 'yes'],
                'robokassa_webhook_url': settings_service.get_setting('robokassa_webhook_url', getattr(settings, 'robokassa_webhook_url', ''))
            }
            
            if request.method == 'POST':
                # Сохраняем настройки в базе данных
                settings_service.set_setting('robokassa_login', request.form.get('robokassa_login', ''))
                settings_service.set_setting('robokassa_password1', request.form.get('robokassa_password1', ''))
                settings_service.set_setting('robokassa_password2', request.form.get('robokassa_password2', ''))
                settings_service.set_setting('robokassa_test_mode', str(request.form.get('robokassa_test_mode', 'true')))
                settings_service.set_setting('robokassa_webhook_url', request.form.get('robokassa_webhook_url', ''))
                
                message = "Настройки успешно сохранены"
                # Обновляем кэш настроек
                settings_service.load_settings_to_cache()
                return render_template('admin/robokassa_settings.html', settings=settings_data, message=message)
            
            return render_template('admin/robokassa_settings.html', settings=settings_data)
        
        @self.app.route('/admin/settings/ai', methods=['GET', 'POST'])
        def admin_ai_settings():
            if not session.get('logged_in'):
                return redirect(url_for('login'))
            
            # Получаем настройки из базы данных
            settings_data = {
                'mistral_api_key': settings_service.get_setting('mistral_api_key', getattr(settings, 'mistral_api_key', '')),
                'mistral_model_name': settings_service.get_setting('mistral_model_name', getattr(settings, 'mistral_model_name', 'mistral-small-latest')),
                'openrouter_api_key': settings_service.get_setting('openrouter_api_key', getattr(settings, 'openrouter_api_key', '')),
                'openrouter_model_name': settings_service.get_setting('openrouter_model_name', getattr(settings, 'openrouter_model_name', 'openchat/openchat-7b')),
                'ai_api_key': settings_service.get_setting('ai_api_key', getattr(settings, 'ai_api_key', ''))
            }
            
            if request.method == 'POST':
                # Сохраняем настройки в базе данных
                settings_service.set_setting('mistral_api_key', request.form.get('mistral_api_key', ''))
                settings_service.set_setting('mistral_model_name', request.form.get('mistral_model_name', 'mistral-small-latest'))
                settings_service.set_setting('openrouter_api_key', request.form.get('openrouter_api_key', ''))
                settings_service.set_setting('openrouter_model_name', request.form.get('openrouter_model_name', 'openchat/openchat-7b'))
                settings_service.set_setting('ai_api_key', request.form.get('ai_api_key', ''))
                
                message = "Настройки успешно сохранены"
                # Обновляем кэш настроек
                settings_service.load_settings_to_cache()
                return render_template('admin/ai_settings.html', settings=settings_data, message=message)
            
            return render_template('admin/ai_settings.html', settings=settings_data)
        
        @self.app.route('/admin/api/stats')
        def admin_api_stats():
            """API endpoint для получения статистики"""
            if not session.get('logged_in'):
                return jsonify({'error': 'Unauthorized'}), 401
            
            db: sessionmaker = SessionLocal()
            try:
                # Статистика за последние 30 дней
                from datetime import timedelta
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                
                # Количество новых пользователей
                new_users = db.query(User).filter(
                    User.created_at >= thirty_days_ago
                ).count()
                
                # Количество сообщений
                messages_count = db.query(ChatHistory).filter(
                    ChatHistory.timestamp >= thirty_days_ago
                ).count()
                
                # Количество транзакций
                transactions_count = db.query(Transaction).filter(
                    Transaction.created_at >= thirty_days_ago
                ).count()
                
                return jsonify({
                    'new_users': new_users,
                    'messages_count': messages_count,
                    'transactions_count': transactions_count
                })
            finally:
                db.close()
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """
        Запускает админ-панель
        """
        self.logger.info("Запуск админ-панели на {}:{}".format(host, port))
        self.app.run(host=host, port=port, debug=debug)


# Создаем экземпляр админ-панели
admin_panel = AdminPanel()