"""
Main entry point for the Telegram bot.
"""

import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Import from other modules
from state import *
from handlers import start, handle_callback, handle_address, add_address, remove_address, list_addresses, home
from monitoring import subscribe_new_tokens, subscribe_trader_activity, subscribe_vybe_trades
from websocket_handlers import on_message, on_error, on_close, on_open

# Load environment variables
load_dotenv()

def main():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("Please set the TELEGRAM_BOT_TOKEN environment variable")

    application = Application.builder().token(bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("home", home))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address))
    
    # Add utility command handlers
    application.add_handler(CommandHandler("add_address", add_address))
    application.add_handler(CommandHandler("remove_address", remove_address))
    application.add_handler(CommandHandler("list_addresses", list_addresses))

    application.run_polling()

if __name__ == "__main__":
    main()