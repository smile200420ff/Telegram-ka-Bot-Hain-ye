"""
Bot initialization and configuration
"""

import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import start, escrow, admin, payment
from utils.database import init_db
from config import BOT_TOKEN

async def create_bot():
    """Create and configure the bot instance"""
    
    # Initialize bot with default properties
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            protect_content=False
        )
    )
    
    # Create dispatcher with memory storage
    dp = Dispatcher(storage=MemoryStorage())
    
    # Initialize database
    await init_db()
    
    # Include routers
    dp.include_router(start.router)
    dp.include_router(escrow.router)
    dp.include_router(admin.router)
    dp.include_router(payment.router)
    
    return bot, dp
