"""
Главный файл Telegram-бота Svetka.
aiogram 3 + polling (dev) или webhook (prod).
"""
import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from core.config import get_settings
from core.backend import backend
from core.cache import close_redis

from middlewares.chat_context import ChatContextMiddleware
from middlewares.anti_flood import AntiFloodMiddleware
from middlewares.soft_mute import SoftMuteMiddleware

from handlers import system, common, admin 
from filters.protection import ProtectionMiddleware
from handlers.triggers import TriggersMiddleware

settings = get_settings()


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="rules", description="Правила группы"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="settings", description="Настройки"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    # Middlewares (порядок важен)
    dp.message.middleware(ChatContextMiddleware())
    dp.message.middleware(SoftMuteMiddleware())
    dp.message.middleware(AntiFloodMiddleware())
    dp.message.middleware(ProtectionMiddleware())
    dp.message.middleware(TriggersMiddleware())

    # Роутеры
    dp.include_router(system.router)
    dp.include_router(common.router)
    dp.include_router(admin.router)

    # Установить команды бота
    await set_bot_commands(bot)

    logger.info("Svetka Bot starting...")
    await backend.log_system("info", "bot", "bot_started", {"env": settings.ENVIRONMENT})

    try:
        if settings.ENVIRONMENT == "production" and settings.BOT_WEBHOOK_URL:
            # Webhook mode
            from aiohttp import web
            from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

            webhook_url = settings.BOT_WEBHOOK_URL
            await bot.set_webhook(webhook_url)
            logger.info(f"Webhook set to {webhook_url}")

            app = web.Application()
            handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
            handler.register(app, path="/webhook")
            setup_application(app, dp, bot=bot)
            web.run_app(app, host="0.0.0.0", port=8001)
        else:
            # Polling mode (development)
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Starting polling...")
            await dp.start_polling(bot)
    finally:
        await backend.close()
        await close_redis()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
