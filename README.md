# MyPal - Solana Trading Monitor Bot

MyPal is a Telegram bot for tracking and monitoring trading activity on the Solana blockchain. It provides real-time notifications about developer activities, token launches, and trader movements, helping users stay ahead of the curve in the fast-paced Solana ecosystem.

## Features

- Track specific traders' wallet activities to monitor their trades in real-time
- Get notifications when tracked traders buy or sell tokens
- Monitor specific token/trader combinations for targeted insights
- Monitor developer wallets for new token deployments on Pump.fun with metadata display
- Track specific developer addresses for real-time trade information on it's deployed token 
- Access comprehensive trade data including price, amounts, and market IDs
- Access Vybe Network's real-time data with detailed information

## Bot Commands

- `/start` - Start the bot and display the main menu
- `/home` - Return to the main menu at any time
- `/add_address <address>` - Add a developer address to your watchlist
- `/remove_address <address>` - Remove an address from your watchlist
- `/list_addresses` - List addresses in your watchlist

## Interactive Features

The bot provides a user-friendly interface with inline buttons for:
- Starting/stopping developer monitoring
- Starting/stopping trader monitoring
- Managing developer wallet tracking
- Managing trader wallet tracking
- Tracking specific trader/token pairs
- Accessing detailed trade information

## Project Structure

```
bot/
├── bot.py                  # Main entry point with command registrations
├── handlers.py             # Command and callback handlers
├── monitoring.py           # Monitoring functions for blockchain activity
├── state.py                # Global state variables and data structures
├── websocket_handlers.py   # WebSocket connection management
└── requirements.txt        # Dependencies
```

## Technical Implementation

- **WebSocket Integration**: Real-time connections to Vybe Network and pump.fun
- **Multi-threading**: Separate threads for WebSocket connections to ensure reliability
- **Error Handling**: Comprehensive error handling with reconnection logic
- **Data Management**: In-memory data structures to manage user watchlists
- **Telegram API**: Utilizes PTB (Python Telegram Bot) for rich message formatting

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd bot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   API_KEY=your_vybe_network_api_key
   WS_URL=wss://api.vybenetwork.xyz/live
   ```

4. Run the bot:
   ```
   python bot.py
   ```

## Usage Guide

1. Start the bot with `/start` or `/home` to access the main menu
2. Select "Dev Tracking" to monitor developer activities:
   - Enter developer wallet addresses to track
   - Click "Start Dev Monitoring" to begin receiving notifications
3. Select "Trader Tracking" to monitor trader activities:
   - Choose "Track All Trades" to monitor all activities of a trader
   - Choose "Track Specific Token" to monitor specific trader/token pairs
   - Click "Start Trader Monitoring" to begin receiving notifications
4. View and manage your watchlists through the "My Watchlists" option

## Dependencies

- python-telegram-bot
- websocket-client
- websockets
- aiohttp
- python-dotenv

## Resources
(MyPal Documentation)[https://mypal.gitbook.io/]

## Demo

Telegram : @mypaldotfun_bot
(link)[https://t.me/mypaldotfun_bot]

