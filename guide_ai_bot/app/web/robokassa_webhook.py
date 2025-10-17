from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import hashlib
import logging

from guide_ai_bot.app.db.models import User, UserBalance, Transaction
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.app.services.payment_service import payment_service
from guide_ai_bot.utils.logger import get_logger


webhook_router = APIRouter()
logger = get_logger(__name__)


async def update_user_balance_async(user_id: int, amount: float):
    """
    Асинхронное обновление баланса пользователя
    """
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

        logger.info(f"Payment successful: user_id={user_id}, amount={amount}", extra={'user_id': user_id})
    except Exception as e:
        logger.error(f"Error updating user balance: {str(e)}", extra={'user_id': user_id, 'error_type': type(e).__name__})
        db.rollback()
    finally:
        db.close()


@webhook_router.post("/webhook/robokassa")
async def robokassa_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook для получения уведомлений от Robokassa
    """
    try:
        # Получаем параметры из запроса
        form_data = await request.form()
        out_sum = form_data.get('OutSum')
        inv_id = form_data.get('InvId')
        signature_value = form_data.get('SignatureValue')

        logger.info(f"Received Robokassa webhook: out_sum={out_sum}, inv_id={inv_id}", extra={'user_id': int(inv_id) if inv_id and inv_id.isdigit() else None})

        # Проверяем и обрабатываем платеж
        if await payment_service.process_payment_notification(out_sum, inv_id, signature_value):
            # Обновляем баланс пользователя в фоновом режиме
            user_id = int(inv_id)
            amount = float(out_sum)
            background_tasks.add_task(update_user_balance_async, user_id, amount)
            logger.info(f"Webhook processed successfully: user_id={user_id}, amount={amount}", extra={'user_id': user_id})
            return "OK"
        else:
            logger.error(f"Invalid signature: out_sum={out_sum}, inv_id={inv_id}", extra={'user_id': int(inv_id) if inv_id and inv_id.isdigit() else None})
            raise HTTPException(status_code=400, detail="Invalid signature")

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", extra={'error_type': type(e).__name__})
        raise HTTPException(status_code=500, detail="Internal server error")