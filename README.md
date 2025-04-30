# Solana Trading Bot

This is a Telegram bot for tracking and monitoring trading activity on Solana blockchain, with a focus on new token deployments and developer activity.

## Features

- Monitor specific developer addresses for new token creations
- Monitor trader wallet activity 
- Track specific token/fee payer combinations for real-time trade information
- Vybe Network API integration for detailed trade data
- Pump.fun integration for new token tracking
- Telegram interface with interactive buttons and commands

## Project Structure

The project is organized in a modular structure for better maintainability:

```
mybot/
├── __init__.py
├── config.py               # Global state and configuration
├── main.py                 # Bot initialization
├── handlers/               # Telegram message handlers
│   ├── __init__.py
│   ├── callback_handlers.py # Inline button handlers
│   ├── command_handlers.py  # Command handlers
│   └── message_handlers.py  # Text message handlers
├── services/               # API integration services
│   ├── __init__.py
│   ├── pump_service.py     # Pump.fun API integration
│   └── vybe_service.py     # Vybe Network API integration
└── utils/                  # Utility functions
    ├── __init__.py
    └── message_utils.py    # Message formatting utilities
```

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API keys:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   API_KEY=your_vybe_network_api_key
   WS_URL=wss://api.vybenetwork.xyz/live
   ```

3. Run the bot:
   ```
   python run.py
   ```

## Commands

- `/start` - Start the bot and display the main menu
- `/add_address <address>` - Add a developer address to your watchlist
- `/remove_address <address>` - Remove an address from your watchlist
- `/list_addresses` - List addresses in your watchlist 