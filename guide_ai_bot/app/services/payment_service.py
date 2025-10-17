import hashlib
from typing import Dict, Optional
from urllib.parse import urlencode
import aiohttp
from datetime import datetime

from guide_ai_bot.core.config import settings
from guide_ai_bot.utils.logger import get_logger


class RobokassaService:
    def __init__(self):
        self.login = settings.robokassa_login
        self.password1 = settings.robokassa_password1
        self.password2 = settings.robokassa_password2
        self.test_mode = settings.robokassa_test_mode
        self.base_url = "https://auth.robokassa.com/" if not self.test_mode else "https://test.robokassa.com/"

    def generate_payment_link(self, user_id: int, amount: float, description: str = "") -> str:
        """
        Генерирует ссылку для оплаты
        """
        # Подготовка параметров
        params = {
            'MerchantLogin': self.login,
            'OutSum': f"{amount:.2f}",
            'InvId': user_id, # Используем user_id как идентификатор заказа
            'Description': description,
            'IsTest': 1 if self.test_mode else 0,
            'Encoding': 'utf-8'
        }

        # Создание подписи
        signature = f"{self.login}:{amount:.2f}:{user_id}:{self.password1}"
        params['SignatureValue'] = hashlib.md5(signature.encode()).hexdigest()

        # Формирование URL
        url = f"{self.base_url}Index.aspx?{urlencode(params)}"
        return url

    def validate_result(self, out_sum: str, inv_id: str, signature_value: str) -> bool:
        """
        Проверяет результат платежа
        """
        expected_signature = hashlib.md5(f"{out_sum}:{inv_id}:{self.password2}".encode()).hexdigest()
        return expected_signature.lower() == signature_value.lower()

    async def process_payment_notification(self, out_sum: str, inv_id: str, signature_value: str) -> bool:
        """
        Обрабатывает уведомление о платеже
        """
        # Проверяем подпись
        if not self.validate_result(out_sum, inv_id, signature_value):
            return False

        # Обновляем баланс пользователя
        user_id = int(inv_id)
        amount = float(out_sum)

        # Вызываем функцию обновления баланса в БД
        await self.update_user_balance(user_id, amount)

        return True

    async def update_user_balance(self, user_id: int, amount: float):
        """
        Асинхронное обновление баланса пользователя
        """
        from sqlalchemy.orm import sessionmaker
        from guide_ai_bot.app.db.models import UserBalance, Transaction
        from guide_ai_bot.app.db.session import SessionLocal
        from datetime import datetime
        from guide_ai_bot.utils.logger import get_logger

        logger = get_logger(__name__)
        db: sessionmaker = SessionLocal()
        try:
            # Получаем или создаем запись баланса
            user_balance = db.query(UserBalance).filter(UserBalance.user_id == user_id).first()
            if not user_balance:
                user_balance = UserBalance(user_id=user_id, balance=0.00)
                db.add(user_balance)

            # Обновляем баланс
            user_balance.balance += amount
            user_balance.last_transaction = datetime.utcnow()

            # Создаем запись транзакции
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                currency="RUB",
                status="completed"
            )
            db.add(transaction)
            db.commit()

            logger.info(f"Balance updated successfully: user_id={user_id}, amount={amount}", extra={'user_id': user_id})
        except Exception as e:
            logger.error(f"Error updating user balance: {str(e)}", extra={'user_id': user_id, 'error_type': type(e).__name__})
            db.rollback()
            raise
        finally:
            db.close()


# Экземпляр сервиса для использования в других модулях
payment_service = RobokassaService()