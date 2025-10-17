from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from guide_ai_bot.core.config import settings

# Создание engine для подключения к базе данных
engine = create_engine(
    settings.database_url,
    echo=True,  # Установите в False в продакшене для отключения логирования SQL-запросов
    pool_pre_ping=True,  # Проверяет соединение перед использованием
    pool_recycle=300, # Пересоздание соединений каждые 300 секунд
)

# Создание sessionmaker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """
    Генератор сессии базы данных для использования в FastAPI/Flask
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()