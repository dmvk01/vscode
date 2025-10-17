# План интеграции Robokassa с Guide_AI_Bot

## Обзор

Для интеграции с Robokassa нужно реализовать:
1. Модуль оплаты (balance module)
2. Обработку платежей
3. Обновление баланса пользователя
4. Webhook для получения уведомлений об успешных платежах

## Шаги реализации

### 1. Добавление модели для баланса пользователя

Создать таблицу `user_balance` в моделях:

```python
class UserBalance(Base):
    __tablename__ = "user_balance"

    user_id = Column(Integer, primary_key=True, ForeignKey("users.user_id"))
    balance = Column(DECIMAL(10, 2), default=0.00)  # Баланс пользователя
    last_transaction = Column(DateTime, default=datetime.utcnow)  # Последняя операция

    # Relationship
    user = relationship("User", back_populates="balance")
```

И обновить модель User, добавив связь:
```python
balance = relationship("UserBalance", back_populates="user", uselist=False, cascade="all, delete-orphan")
```

### 2. Настройка конфигурации

Добавить в .env файл переменные для Robokassa:

```env
ROBOKASSA_LOGIN=your_login
ROBOKASSA_PASSWORD1=your_password1
ROBOKASSA_PASSWORD2=your_password2
ROBOKASSA_TEST_MODE=true  # Для тестирования
ROBOKASSA_WEBHOOK_URL=https://yourdomain.com/webhook/robokassa
```

### 3. Создание сервиса для работы с Robokassa

Создать `guide_ai_bot/app/services/payment_service.py`:

```python
import hashlib
from typing import Dict, Optional
from urllib.parse import urlencode
import aiohttp

from guide_ai_bot.core.config import settings


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
            'OutSum': amount,
            'InvId': user_id,  # Используем user_id как идентификатор заказа
            'Description': description,
            'IsTest': 1 if self.test_mode else 0,
            'Encoding': 'utf-8'
        }

        # Создание подписи
        signature = f"{self.login}:{amount}:{user_id}:{self.password1}"
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

        # Здесь нужно вызвать функцию обновления баланса в БД
        # await update_user_balance(user_id, amount)

        return True
```

### 4. Создание обработчика команды /balance

Создать или обновить `guide_ai_bot/app/bot/handlers/balance.py`:

```python
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.orm import sessionmaker

from guide_ai_bot.app.db.models import User, UserBalance
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.app.services.payment_service import RobokassaService


balance_router = Router()


@balance_router.message(Command("balance"))
async def balance_handler(message: types.Message):
    """
    Обработчик команды /balance
    Показывает текущий баланс и предлагает пополнить
    """
    user_id = message.from_user.id

    # Создаем сессию для работы с базой данных
    db: sessionmaker = SessionLocal()

    try:
        # Получаем пользователя из базы данных
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            await message.answer("Ошибка: Пользователь не найден")
            return

        # Получаем баланс пользователя
        user_balance = db.query(UserBalance).filter(UserBalance.user_id == user_id).first()
        current_balance = user_balance.balance if user_balance else 0.00

        # Формируем сообщение
        balance_message = f"Ваш текущий баланс: {current_balance} RUB\n\n"
        balance_message += "Для пополнения баланса выберите сумму:"

        # Кнопки для быстрого пополнения
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="50 RUB", callback_data="recharge_50"),
                types.InlineKeyboardButton(text="100 RUB", callback_data="recharge_100")
            ],
            [
                types.InlineKeyboardButton(text="500 RUB", callback_data="recharge_500"),
                types.InlineKeyboardButton(text="1000 RUB", callback_data="recharge_1000")
            ]
        ])

        await message.answer(balance_message, reply_markup=keyboard)

    finally:
        # Закрываем сессию
        db.close()


@balance_router.callback_query(lambda c: c.data.startswith("recharge_"))
async def process_recharge_callback(callback_query: types.CallbackQuery):
    """
    Обработка нажатия на кнопки пополнения
    """
    amount = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id

    # Создаем сервис оплаты
    payment_service = RobokassaService()

    # Генерируем ссылку для оплаты
    payment_url = payment_service.generate_payment_link(
        user_id=user_id,
        amount=amount,
        description=f"Пополнение баланса на {amount} RUB"
    )

    # Отправляем пользователю ссылку для оплаты
    await callback_query.message.answer(
        f"Для пополнения баланса на {amount} RUB перейдите по ссылке:\n{payment_url}"
    )

    await callback_query.answer()
```

### 5. Создание эндпоинта для webhook

Создать `guide_ai_bot/app/web/robokassa_webhook.py`:

```python
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import sessionmaker
import logging

from guide_ai_bot.app.db.models import User, UserBalance, Transaction
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.app.services.payment_service import RobokassaService


webhook_router = APIRouter()
logger = logging.getLogger(__name__)


@webhook_router.post("/webhook/robokassa")
async def robokassa_webhook(request: Request):
    """
    Webhook для получения уведомлений от Robokassa
    """
    try:
        # Получаем параметры из запроса
        form_data = await request.form()
        out_sum = form_data.get('OutSum')
        inv_id = form_data.get('InvId')
        signature_value = form_data.get('SignatureValue')

        # Создаем сервис оплаты
        payment_service = RobokassaService()

        # Проверяем и обрабатываем платеж
        if payment_service.process_payment_notification(out_sum, inv_id, signature_value):
            # Обновляем баланс пользователя
            db: sessionmaker = SessionLocal()
            try:
                user_id = int(inv_id)
                amount = float(out_sum)

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

                logger.info(f"Payment successful: user_id={user_id}, amount={amount}")
                return "OK"
            finally:
                db.close()
        else:
            logger.error(f"Invalid signature: out_sum={out_sum}, inv_id={inv_id}")
            raise HTTPException(status_code=400, detail="Invalid signature")

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 6. Обновление конфигурации приложения

В `guide_ai_bot/core/config.py` добавить:

```python
class Settings(BaseSettings):
    # ... существующие поля ...
    robokassa_login: str = ""
    robokassa_password1: str = ""
    robokassa_password2: str = ""
    robokassa_test_mode: bool = True
    robokassa_webhook_url: str = ""
```

### 7. Обновление структуры проекта

Создать недостающие файлы и обновить структуру:
- `guide_ai_bot/app/services/payment_service.py` - сервис оплаты
- `guide_ai_bot/app/bot/handlers/balance.py` - обработчик баланса
- `guide_ai_bot/app/web/robokassa_webhook.py` - webhook
- Обновить `guide_ai_bot/app/db/models.py` - добавить UserBalance
- Обновить `guide_ai_bot/core/config.py` - добавить настройки Robokassa

### 8. Миграция базы данных

Создать миграцию для добавления таблицы user_balance:

```bash
python -m alembic revision --autogenerate -m "Add user_balance table"
python -m alembic upgrade head
```

### 9. Тестирование

1. Настроить тестовый аккаунт в Robokassa
2. Заполнить .env файл тестовыми данными
3. Проверить генерацию ссылок на оплату
4. Проверить обработку webhook
5. Проверить обновление баланса

## Безопасность

1. Валидация подписей платежей
2. Проверка суммы и идентификатора пользователя
3. Защита от дублирования транзакций
4. Логирование всех операций

## Особенности

1. В тестовом режиме Robokassa позволяет проводить тестовые платежи
2. Webhook должен быть доступен из интернета (при локальной разработке использовать ngrok)
3. Все транзакции должны быть логированы
4. Необходима обработка ошибок и исключений