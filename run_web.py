import uvicorn
from guide_ai_bot.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "guide_ai_bot.app.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.debug,  # В production режиме отключаем hot reload
    )