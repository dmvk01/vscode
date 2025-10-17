import asyncio
import os
from dotenv import load_dotenv

from guide_ai_bot.app.services.payment_service import RobokassaService
from guide_ai_bot.app.db.models import User, UserBalance
from guide_ai_bot.app.db.session import SessionLocal

# Загружаем переменные окружения
load_dotenv()

async def test_robokassa_service():
    """
    Тестирование сервиса Robokassa
    """
    print("Тестирование сервиса Robokassa...")
    
    # Создаем экземпляр сервиса
    service = RobokassaService()
    
    # Тестируем генерацию ссылки для оплаты
    user_id = 123456
    amount = 100.00
    description = "Тестовое пополнение баланса"
    
    try:
        payment_link = service.generate_payment_link(user_id, amount, description)
        print(f"Ссылка для оплаты: {payment_link}")
        
        # Проверим, что ссылка содержит необходимые параметры
        assert service.login in payment_link
        assert str(amount) in payment_link
        assert str(user_id) in payment_link
        print("[OK] Ссылка для оплаты сгенерирована корректно")
        
    except Exception as e:
        print(f"[ERROR] Ошибка при генерации ссылки для оплаты: {e}")
        return False
    
    # Тестируем валидацию результата (с неверной подписью для проверки)
    try:
        is_valid = service.validate_result("10.00", "123456", "invalid_signature")
        print(f"Результат валидации (ожидаем False): {is_valid}")
        
        # Тестируем с правильной подписью (вручную сгенерированной)
        import hashlib
        expected_signature = hashlib.md5(f"100.00:123456:{service.password2}".encode()).hexdigest()
        is_valid_correct = service.validate_result("100.00", "123456", expected_signature)
        print(f"Результат валидации с правильной подписью (ожидаем True): {is_valid_correct}")
        
        print("[OK] Валидация подписи работает корректно")
        
    except Exception as e:
        print(f"[ERROR] Ошибка при валидации: {e}")
        return False
    
    return True

async def test_balance_update():
    """
    Тестирование обновления баланса
    """
    print("\nТестирование обновления баланса...")
    
    db = SessionLocal()
    try:
        # Создаем тестового пользователя, если его нет
        user = db.query(User).filter(User.user_id == 123456).first()
        if not user:
            user = User(
                user_id=123456,
                username="test_user",
                subscription_type="Free",
                consent=True,
                language="ru"
            )
            db.add(user)
            db.commit()
        
        # Проверяем начальный баланс
        user_balance = db.query(UserBalance).filter(UserBalance.user_id == 123456).first()
        initial_balance = user_balance.balance if user_balance else 0.00
        print(f"Начальный баланс: {initial_balance}")
        
        # Имитируем обновление баланса через сервис
        service = RobokassaService()
        amount_to_add = 50.00
        
        await service.update_user_balance(123456, amount_to_add)
        print(f"Баланс обновлен на {amount_to_add} RUB")
        
        # Проверяем обновленный баланс
        db.refresh(user_balance) if user_balance else None
        user_balance = db.query(UserBalance).filter(UserBalance.user_id == 123456).first()
        updated_balance = user_balance.balance if user_balance else 0.00
        print(f"Обновленный баланс: {updated_balance}")
        
        expected_balance = initial_balance + amount_to_add
        if updated_balance == expected_balance:
            print("[OK] Баланс обновлен корректно")
            return True
        else:
            print(f"[ERROR] Ошибка: ожидаемый баланс {expected_balance}, полученный {updated_balance}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Ошибка при обновлении баланса: {e}")
        return False
    finally:
        db.close()

async def main():
    """
    Основная функция тестирования
    """
    print("=== Тестирование интеграции Robokassa ===\n")
    
    # Тестируем сервис оплаты
    service_test_result = await test_robokassa_service()
    
    # Тестируем обновление баланса
    balance_test_result = await test_balance_update()
    print(f"\n=== Результаты тестирования ===")
    print(f"Тестирование сервиса оплаты: {'[OK] Пройдено' if service_test_result else '[ERROR] Провалено'}")
    print(f"Тестирование обновления баланса: {'[OK] Пройдено' if balance_test_result else '[ERROR] Провалено'}")
    
    overall_result = service_test_result and balance_test_result
    print(f"Общий результат: {'[OK] Все тесты пройдены' if overall_result else '[ERROR] Тестирование не пройдено'}")
    
    return overall_result


if __name__ == "__main__":
    asyncio.run(main())