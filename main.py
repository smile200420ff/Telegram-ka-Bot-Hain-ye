#!/usr/bin/env python3
"""
Quick Escrow Bot - Main Entry Point
Cyberpunk-themed Telegram bot for secure escrow transactions
"""

import asyncio
import logging
import os
from bot import create_bot
from config import BOT_TOKEN

# Configure logging with cyberpunk styling
logging.basicConfig(
    level=logging.INFO,
    format='[🔐 %(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('escrow_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    try:
        logger.info("🚀 Initializing Quick Escrow Bot...")
        
        # Create and start the bot
        bot, dp = await create_bot()
        
        logger.info("⚡ Bot initialized successfully!")
        logger.info("🔥 Starting polling...")
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
