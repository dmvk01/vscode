from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)  # Telegram User ID
    username = Column(String(255))
    subscription_type = Column(String(50), default="Free")  # Free/Premium
    subscription_end_date = Column(DateTime)
    current_module = Column(String(50), default=None)  # Активный модуль (chat, horoscope, battle и т.п.)
    birth_date = Column(DateTime, default=None)  # Дата рождения для персонализации (опционально)
    consent = Column(Boolean, default=None)  # Согласие на хранение и обработку данных
    language = Column(String(5), default="ru")  # Язык (ru/en, default: ru)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat_history = relationship("ChatHistory", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    user_modules = relationship("UserModule", back_populates="user")
    balance = relationship("UserBalance", back_populates="user", uselist=False, cascade="all, delete-orphan")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    history_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_system = Column(Boolean, default=False)  # Поле для обозначения системных сообщений

    # Relationship
    user = relationship("User", back_populates="chat_history")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    amount = Column(DECIMAL(10, 2))
    currency = Column(String(10))
    status = Column(String(20), default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="transactions")


class Module(Base):
    __tablename__ = "modules"

    module_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    description = Column(Text)
    price = Column(DECIMAL(10, 2))

    # Relationship
    user_modules = relationship("UserModule", back_populates="module")


class UserModule(Base):
    __tablename__ = "user_modules"

    user_module_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    module_id = Column(Integer, ForeignKey("modules.module_id"))
    is_active = Column(Boolean, default=False)
    activation_date = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="user_modules")
    module = relationship("Module", back_populates="user_modules")


class UserBalance(Base):
    __tablename__ = "user_balance"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    balance = Column(DECIMAL(10, 2), default=0.00)  # Баланс пользователя
    last_transaction = Column(DateTime, default=datetime.utcnow)  # Последняя операция

    # Relationship
    user = relationship("User", back_populates="balance")


class Setting(Base):
    """
    Модель для хранения конфигурационных настроек в базе данных
    """
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True)  # Ключ настройки
    value = Column(Text)  # Значение настройки
    description = Column(Text)  # Описание настройки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)