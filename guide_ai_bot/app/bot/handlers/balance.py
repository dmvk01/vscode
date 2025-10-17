from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.orm import sessionmaker

from guide_ai_bot.app.db.models import User, UserBalance
from guide_ai_bot.app.db.session import SessionLocal
from guide_ai_bot.app.services.payment_service import payment_service


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
        balance_message = f"Ваш текущий баланс: {current_balance:.2f} RUB\n\n"
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
            ],
            [
                types.InlineKeyboardButton(text="Другая сумма", callback_data="recharge_other")
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
    action = callback_query.data.split("_")[1]
    
    if action == "other":
        # Обработка выбора "Другая сумма"
        await callback_query.message.answer("Введите сумму для пополнения баланса:")
        # Здесь в реальном приложении нужно добавить логику обработки ввода суммы
    else:
        try:
            amount = int(action)
            user_id = callback_query.from_user.id

            # Генерируем ссылку для оплаты
            payment_url = payment_service.generate_payment_link(
                user_id=user_id,
                amount=amount,
                description=f"Пополнение баланса на {amount} RUB"
            )

            # Отправляем пользователю ссылку для оплаты
            await callback_query.message.answer(
                f"Для пополнения баланса на {amount} RUB перейдите по ссылке:\n{payment_url}\n\n"
                f"После оплаты ваш баланс будет автоматически обновлен."
            )
        except ValueError:
            await callback_query.message.answer("Ошибка: некорректная сумма")

    await callback_query.answer()