from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from core.database import engine, Base
from core.redis import get_redis, close_redis
from api import chats, settings, moderation, triggers, analytics, logs, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Svetka Backend...")
    # Инициализация Redis
    await get_redis()
    yield
    await close_redis()
    await engine.dispose()
    logger.info("Svetka Backend stopped.")


app = FastAPI(
    title="Svetka API",
    description="Backend API для Telegram-бота Svetka",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(chats.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(moderation.router, prefix="/api/v1")
app.include_router(triggers.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "svetka-backend"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Endpoint для Telegram webhook — перенаправляем в бот."""
    return {"ok": True}
