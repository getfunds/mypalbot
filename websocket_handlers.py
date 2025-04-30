"""
WebSocket handler functions for managing real-time data connections.
"""

import json
import threading
import asyncio
from datetime import datetime
from state import trader_watchlists

# Define the websocket message handler function (will run in a separate thread)
def on_message(ws_app, message_str, user_id, token_mint, context, loop):
    print(f"Thread {threading.get_ident()} received message: {message_str[:150]}...")
    try:
        trade_data = json.loads(message_str)
        # Determine if token was bought or sold
        trade_base_mint = trade_data.get('baseMintAddress', '')
        if trade_base_mint == token_mint:
            trade_type = "Token Sold"
            trade_emoji = "🔴"
        else:
            trade_type = "Token Bought"
            trade_emoji = "🟢"

        # Format trade data
        formatted_message = (
            f"{trade_emoji} <b>{trade_type}</b>\n\n"
            f"<b>Token:</b><a href='https://vybe.fyi/tokens/{token_mint}'> {token_mint}\n</a>"
            f"<b >Fee Payer:</b><a href='https://vybe.fyi/wallets/{trade_data.get('feePayer', '')}'> {trade_data.get('feePayer', 'Unknown')}\n</a>"
            f"<b>Time:</b> {datetime.fromtimestamp(trade_data.get('blockTime', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"<b>Price:</b> {float(trade_data.get('price', 0)) / 100000:.6f}\n"
            f"<b>Base Amount:</b> {float(trade_data.get('baseSize', 0)):.6f}\n"
            f"<b>Quote Amount:</b> {float(trade_data.get('quoteSize', 0)):.6f}\n"
            f"<b >Base Token: </b><a href='https://vybe.fyi/tokens/{trade_data.get('baseMintAddress', '')}'> {trade_data.get('baseMintAddress', 'Unknown')}\n</a>"
            f"<b >Quote Token: </b><a href='https://vybe.fyi/tokens/{trade_data.get('quoteMintAddress', '')}'>{trade_data.get('quoteMintAddress', 'Unknown')}\n\n</a>"
            f"<b >Markets ID: </b><a href='https://vybe.fyi/wallets/{trade_data.get('marketId', '')}'>{trade_data.get('marketId', 'Unknown')}\n\n</a>"
            f"<a href='https://solscan.io/tx/{trade_data.get('signature', '')}'>View Transaction</a>"
        )

        # Use the passed loop object for scheduling the coroutine
        if loop:
            asyncio.run_coroutine_threadsafe(
                context.bot.send_message(chat_id=user_id, text=formatted_message, parse_mode='HTML'),
                loop
            )
        else:
             print(f"Error: No event loop passed to on_message for thread {threading.get_ident()}")

    except json.JSONDecodeError as e:
        print(f"Thread {threading.get_ident()} JSON decode error: {e} - Message: {message_str}")
    except Exception as e:
        print(f"Thread {threading.get_ident()} Error processing message: {e}")

# Define error handler
def on_error(ws_app, error):
    print(f"WebSocket Error (Thread {threading.get_ident()}): {error}")

# Define close handler
def on_close(ws_app, close_status_code, close_msg):
    print(f"WebSocket Closed (Thread {threading.get_ident()}): Status {close_status_code}, Msg: {close_msg}")

# Define open handler (sends config message)
def on_open(ws_app, token_mint, fee_payer):
    print(f"WebSocket Connection Opened (Thread {threading.get_ident()})")
    try:
        config_message = {
            "type": "configure",
            "filters": {
                "trades": [{
                    "tokenMintAddress": token_mint,
                    "feePayer": fee_payer
                }]
            }
        }
        ws_app.send(json.dumps(config_message))
        print(f"Configuration message sent: {json.dumps(config_message)}")
    except Exception as e:
        print(f"Error sending config message in on_open: {e}")

# Define trader message handler
def on_message_trader(ws_app, message_str, user_id, context, loop):
    print(f"Thread {threading.get_ident()} received trader message: {message_str[:150]}...")
    try:
        trade_data = json.loads(message_str)
        
        # Check if the fee payer is in the user's trader watchlist
        fee_payer = trade_data.get('feePayer', '')
        if fee_payer not in trader_watchlists.get(user_id, set()):
            return  # Skip if not in watchlist
        
        # Determine if token was bought or sold based on base_mint
        # SOL's mint address - if base_mint is SOL, user is buying the other token
        SOL_MINT = "So11111111111111111111111111111111111111112"
        base_mint = trade_data.get('baseMintAddress', '')
        
        if base_mint == SOL_MINT:
            trade_type = "Token Bought"  # Buying with SOL
            trade_emoji = "🟢"
        else:
            trade_type = "Token Sold"  # Selling for SOL or other token
            trade_emoji = "🔴"

        # Format trade data
        formatted_message = (
            f"{trade_emoji} <b>{trade_type}</b>\n\n"
            f"<b>Trader:</b><a href='https://vybe.fyi/wallets/{fee_payer}'>{fee_payer}\n</a>"
            f"<b>Time:</b> {datetime.fromtimestamp(trade_data.get('blockTime', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"<b>Price:</b> {float(trade_data.get('price', 0)) / 100000:.6f}\n"
            f"<b>Base Amount:</b> {float(trade_data.get('baseSize', 0)):.6f}\n"
            f"<b>Quote Amount:</b> {float(trade_data.get('quoteSize', 0)):.6f}\n"
            f"<b >Base Token: </b><a href='https://vybe.fyi/tokens/{trade_data.get('baseMintAddress', '')}'> {trade_data.get('baseMintAddress', 'Unknown')}\n</a>"
            f"<b >Quote Token: </b><a href='https://vybe.fyi/tokens/{trade_data.get('quoteMintAddress', '')}'>{trade_data.get('quoteMintAddress', 'Unknown')}\n\n</a>"
            f"<b >Markets ID: </b><a href='https://vybe.fyi/wallets/{trade_data.get('marketId', '')}'>{trade_data.get('marketId', 'Unknown')}\n\n</a>"
            f"<a href='https://solscan.io/tx/{trade_data.get('signature', '')}'>View Transaction</a>"
        )

        # Use the passed loop object for scheduling the coroutine
        if loop:
            asyncio.run_coroutine_threadsafe(
                context.bot.send_message(chat_id=user_id, text=formatted_message, parse_mode='HTML'),
                loop
            )
        else:
             print(f"Error: No event loop passed to on_message_trader for thread {threading.get_ident()}")

    except json.JSONDecodeError as e:
        print(f"Thread {threading.get_ident()} JSON decode error: {e} - Message: {message_str}")
    except Exception as e:
        print(f"Thread {threading.get_ident()} Error processing trader message: {e}")

# Define trader open handler
def on_open_trader(ws_app, user_id):
    print(f"Trader WebSocket Connection Opened (Thread {threading.get_ident()})")
    try:
        # Get all trader addresses from the user's watchlist
        trader_addresses = list(trader_watchlists.get(user_id, set()))
        
        if not trader_addresses:
            print(f"No trader addresses in watchlist for user {user_id}")
            return
            
        config_message = {
            "type": "configure",
            "filters": {
                "trades": [{
                    "feePayer": address
                } for address in trader_addresses]
            }
        }
        ws_app.send(json.dumps(config_message))
        print(f"Trader configuration message sent: {json.dumps(config_message)}")
    except Exception as e:
        print(f"Error sending trader config message in on_open_trader: {e}") 