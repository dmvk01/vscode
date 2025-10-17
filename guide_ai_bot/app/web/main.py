from fastapi import FastAPI
from guide_ai_bot.app.web.robokassa_webhook import webhook_router
from guide_ai_bot.app.db.session import engine
from guide_ai_bot.app.db.models import Base

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Создаем экземпляр FastAPI
app = FastAPI(title="Guide_AI_Bot Webhooks")

# Подключаем маршруты
app.include_router(webhook_router)

# Маршрут для проверки работоспособности
@app.get("/")
def read_root():
    return {"status": "Guide_AI_Bot webhook service is running"}

# Маршрут для проверки вебхука
@app.get("/webhook/robokassa")
def check_webhook():
    return {"status": "Robokassa webhook is available"}