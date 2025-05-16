"""
Monitoring functions for tracking tokens, developers, and traders.
"""

import asyncio
import json
import os
import threading
import uuid
import websockets
import aiohttp
import websocket
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Import from other modules
from state import user_watchlists, active_monitoring, trader_watchlists, active_trader_monitoring, pending_vybe_tracks, dev_trade_watchlists, trader_token_watchlists
from websocket_handlers import on_message, on_error, on_close, on_open, on_open_trader, on_message_trader

# Define a function similar to on_open but with both fee payer and token mint
def on_open_trader_token(ws_app, trader_address, token_mint):
    print(f"Trader-Token WebSocket Connection Opened (Thread {threading.get_ident()})")
    try:
        config_message = {
            "type": "configure",
            "filters": {
                "trades": [{
                    "tokenMintAddress": token_mint,
                    "feePayer": trader_address
                }]
            }
        }
        ws_app.send(json.dumps(config_message))
        print(f"Trader-Token configuration message sent: {json.dumps(config_message)}")
    except Exception as e:
        print(f"Error sending Trader-Token config message in on_open_trader_token: {e}")

async def subscribe_trader_token_activity(user_id: int, trader_address: str, token_mint: str, context):
    """
    Monitor trading activity for a specific trader and token using Vybe Network WebSocket.
    """
    api_key = os.getenv('API_KEY')
    websocket_uri = os.getenv('WS_URL', "wss://api.vybenetwork.xyz/live")

    if not api_key or not websocket_uri:
        print("API_KEY or WS_URL missing in .env")
        return

    print(f"Setting up Vybe WebSocket for trader-token monitoring: Trader={trader_address}, Token={token_mint}")

    # Get the current event loop *before* starting the thread
    main_loop = asyncio.get_running_loop()

    while user_id in active_trader_monitoring:
        ws_app = None
        ws_thread = None
        try:
            custom_headers = {"X-API-Key": api_key} # Format for websocket-client

            # Create WebSocketApp instance
            ws_app = websocket.WebSocketApp(
                websocket_uri,
                header=custom_headers,
                on_open=lambda ws: on_open_trader_token(ws, trader_address, token_mint),
                on_message=lambda ws, msg: on_message(ws, msg, user_id, token_mint, context, main_loop),
                on_error=on_error,
                on_close=on_close
            )

            # Start the WebSocket connection in a separate daemon thread
            ws_thread = threading.Thread(target=ws_app.run_forever, daemon=True)
            print(f"Starting Vybe WebSocket thread for trader-token monitoring: {ws_thread.name}...")
            ws_thread.start()

            # Keep the async task alive while the thread is running and user is monitoring
            while (user_id in active_trader_monitoring and 
                   ws_thread.is_alive() and 
                   user_id in trader_token_watchlists and 
                   trader_address in trader_token_watchlists[user_id]):
                await asyncio.sleep(1) # Check every second

            # If we stopped because the trader-token pair was removed
            if (user_id in active_trader_monitoring and ws_thread.is_alive() and 
                (user_id not in trader_token_watchlists or trader_address not in trader_token_watchlists[user_id])):
                print(f"Trader-Token pair {trader_address}→{token_mint} removed, stopping monitoring")
                if ws_app:
                    ws_app.close()
                break

            # If loop exits, either user stopped monitoring or thread died
            if not ws_thread.is_alive():
                print(f"WebSocket thread {ws_thread.name} died unexpectedly.")
                if user_id in active_trader_monitoring:
                    print("Attempting to restart WebSocket thread...")
                else:
                    print("User stopped monitoring while thread was dead.")
            else: # User must have stopped monitoring
                 print(f"User {user_id} stopped monitoring. Shutting down WebSocket thread {ws_thread.name}...")
                 if ws_app: # Ensure ws_app exists before calling close
                    ws_app.close() # Gracefully close the connection
                 ws_thread.join(timeout=5) # Wait for thread to close
                 if ws_thread.is_alive():
                     print(f"Warning: WebSocket thread {ws_thread.name} did not terminate gracefully.")
                 break # Exit the outer while loop

        except Exception as e:
            print(f"Error setting up or managing WebSocket thread: {e}")
            # Ensure cleanup even on setup errors
            if ws_app:
                ws_app.close()
            if ws_thread and ws_thread.is_alive():
                ws_thread.join(timeout=1)

        # Wait before restarting the loop (if applicable)
        if user_id in active_trader_monitoring:
            # Check if the trader-token pair is still in watchlist
            if (user_id not in trader_token_watchlists or 
                trader_address not in trader_token_watchlists[user_id]):
                print(f"Trader-Token pair {trader_address}→{token_mint} no longer in user's watchlist, stopping monitoring")
                break
            
            print("Waiting 5 seconds before restarting WebSocket connection attempt...")
            await asyncio.sleep(5)
        else:
             break # Exit if user stopped monitoring during error/cleanup

    print(f"Exiting subscribe_trader_token_activity task for user {user_id}, trader {trader_address}, token {token_mint}")

async def subscribe_new_tokens(user_id: int, context):
    uri = "wss://pumpportal.fun/api/data"

    while user_id in active_monitoring:
        try:
            async with websockets.connect(uri) as websocket:
                payload = {"method": "subscribeNewToken"}
                await websocket.send(json.dumps(payload))

                while user_id in active_monitoring:
                    try:
                        message = await websocket.recv()
                        token_data = json.loads(message)

                        if token_data.get('traderPublicKey') in user_watchlists.get(user_id, set()):
                            # --- Existing message formatting logic ---
                            metadata = {}
                            image_url = None
                            if token_data.get('uri'):
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(token_data['uri']) as response:
                                        if response.status == 200:
                                            try:
                                                metadata = await response.json()
                                                if 'image' in metadata:
                                                    image_url = metadata['image']
                                            except aiohttp.ContentTypeError:
                                                print(f"Warning: Non-JSON response for metadata URI {token_data['uri']}")
                                                metadata = {} # Reset metadata if JSON parsing fails

                            formatted_message = (
                                f"<u>Token Info (Pump.fun):</u>\n\n"
                                f"<b>{token_data['name']}</b>\n"
                            )
                            if metadata.get('description'):
                                formatted_message += f"{metadata['description']}\n\n"
                            formatted_message += (
                                f"Token Address: {token_data['mint']}\n"
                                f"Ticker: {token_data['symbol']}\n"
                                f"Dev Buy: {token_data['solAmount']} SOL\n"
                                f"Dev Address: {token_data['traderPublicKey']}\n\n"
                            )
                            social_links = []
                            if metadata.get('twitter'):
                                social_links.append(f"<a href='{metadata['twitter']}'>X/Twitter</a>")
                            if metadata.get('website'):
                                social_links.append(f"<a href='{metadata['website']}'>Website</a>")
                            if metadata.get('telegram'):
                                social_links.append(f"<a href='{metadata['telegram']}'>Telegram</a>")
                            if social_links:
                                formatted_message += f"{' | '.join(social_links)}\n\n"
                            formatted_message += (
                                f"<a href='https://pump.fun/coin/{token_data['mint']}'>Pump.fun</a> | "
                                f"<a href='https://solscan.io/tx/{token_data['signature']}'>Mint TX</a>"
                            )
                            # --- End of existing formatting ---

                            # --- Add Button Logic ---
                            token_mint = token_data.get('mint')
                            fee_payer = token_data.get('traderPublicKey') # Dev address as fee payer

                            if token_mint and fee_payer:
                                track_id = uuid.uuid4().hex[:10] # Generate short unique ID
                                lookup_key = f"{user_id}:{track_id}"
                                pending_vybe_tracks[lookup_key] = {'mint': token_mint, 'dev': fee_payer}
                                print(f"Stored pending track: {lookup_key} -> {pending_vybe_tracks[lookup_key]}") # Debug print

                                # Create the button
                                keyboard = InlineKeyboardMarkup([[
                                    InlineKeyboardButton("📊 Track Dev (Vybe)", callback_data=f"track_dev_vybe:{track_id}")
                                ]])
                            else:
                                keyboard = None # Don't add button if data is missing

                            # Send message with button
                            await context.bot.send_photo(
                                chat_id=user_id,
                                photo=image_url or "https://via.placeholder.com/150", # Provide a default image if None
                                caption=formatted_message,
                                parse_mode='HTML',
                                reply_markup=keyboard # Add the keyboard here
                            )
                            # --- End of Button Logic ---

                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error processing token in subscribe_new_tokens: {e}")
                        continue

        except websockets.exceptions.ConnectionClosed:
             if user_id in active_monitoring:
                 # Avoid sending message if user intentionally stopped monitoring
                 if user_id in active_monitoring:
                     await context.bot.send_message(
                         chat_id=user_id,
                         text="Pump.fun connection closed. Reconnecting..."
                     )
                 await asyncio.sleep(5)
        except Exception as e:
             if user_id in active_monitoring:
                 # Avoid sending message if user intentionally stopped monitoring
                 if user_id in active_monitoring:
                     await context.bot.send_message(
                         chat_id=user_id,
                         text=f"An error occurred with Pump.fun connection: {e}"
                     )
                 await asyncio.sleep(5)

async def subscribe_trader_activity(user_id: int, context, specific_trader=None):
    """
    Monitor trading activity for addresses in the trader watchlist using Vybe Network WebSocket.
    Similar to subscribe_vybe_trades but without token mint filtering.
    
    If specific_trader is provided, only monitor that trader's activity.
    """
    api_key = os.getenv('API_KEY')
    websocket_uri = os.getenv('WS_URL', "wss://api.vybenetwork.xyz/live")

    if not api_key or not websocket_uri:
        print("API_KEY or WS_URL missing in .env")
        return

    print(f"Setting up Vybe WebSocket for trader monitoring for user {user_id}{' for specific trader: ' + specific_trader if specific_trader else ''}")

    # Get the current event loop *before* starting the thread
    main_loop = asyncio.get_running_loop()

    while user_id in active_trader_monitoring:
        ws_app = None
        ws_thread = None
        try:
            custom_headers = {"X-API-Key": api_key} # Format for websocket-client

            # Create WebSocketApp instance
            if specific_trader:
                # For a specific trader, we need a custom on_open function
                def on_open_specific_trader(ws):
                    print(f"Trader WebSocket Connection Opened for specific trader: {specific_trader}")
                    try:
                        config_message = {
                            "type": "configure",
                            "filters": {
                                "trades": [{
                                    "feePayer": specific_trader
                                }]
                            }
                        }
                        ws.send(json.dumps(config_message))
                        print(f"Specific trader configuration message sent: {json.dumps(config_message)}")
                    except Exception as e:
                        print(f"Error sending specific trader config message: {e}")
                
                on_open_func = on_open_specific_trader
            else:
                # Use the standard on_open_trader function for all traders
                on_open_func = lambda ws: on_open_trader(ws, user_id)

            # Create WebSocketApp instance
            ws_app = websocket.WebSocketApp(
                websocket_uri,
                header=custom_headers,
                on_open=on_open_func,
                on_message=lambda ws, msg: on_message_trader(ws, msg, user_id, context, main_loop),
                on_error=on_error,
                on_close=on_close
            )

            # Start the WebSocket connection in a separate daemon thread
            ws_thread = threading.Thread(target=ws_app.run_forever, daemon=True)
            print(f"Starting Vybe WebSocket thread for trader monitoring: {ws_thread.name}...")
            ws_thread.start()

            # Keep the async task alive while the thread is running and user is monitoring
            # If monitoring a specific trader, also check if that trader is still in the watchlist
            while user_id in active_trader_monitoring and ws_thread.is_alive():
                if specific_trader and user_id in trader_watchlists and specific_trader not in trader_watchlists[user_id]:
                    print(f"Trader {specific_trader} was removed from watchlist, stopping specific monitoring")
                    if ws_app:
                        ws_app.close()
                    break
                await asyncio.sleep(1) # Check every second

            # If loop exits, either user stopped monitoring or thread died
            if not ws_thread.is_alive():
                print(f"Vybe WebSocket thread {ws_thread.name} died unexpectedly.")
                if user_id in active_trader_monitoring:
                    print("Attempting to restart Vybe WebSocket thread...")
                else:
                    print("User stopped monitoring while thread was dead.")
            else: # User must have stopped monitoring
                 print(f"User {user_id} stopped monitoring. Shutting down Vybe WebSocket thread {ws_thread.name}...")
                 if ws_app: # Ensure ws_app exists before calling close
                    ws_app.close() # Gracefully close the connection
                 ws_thread.join(timeout=5) # Wait for thread to close
                 if ws_thread.is_alive():
                     print(f"Warning: Vybe WebSocket thread {ws_thread.name} did not terminate gracefully.")
                 break # Exit the outer while loop

        except Exception as e:
            print(f"Error setting up or managing Vybe WebSocket thread: {e}")
            # Ensure cleanup even on setup errors
            if ws_app:
                ws_app.close()
            if ws_thread and ws_thread.is_alive():
                ws_thread.join(timeout=1)

        # Wait before restarting the loop (if applicable)
        if user_id in active_trader_monitoring:
            # Check if the dev is still in dev_trade_watchlist if applicable
            if specific_trader and specific_trader not in trader_watchlists.get(user_id, set()):
                print(f"Trader {specific_trader} no longer in user's trader watchlist, stopping monitoring")
                break
            
            print("Waiting 5 seconds before restarting Vybe WebSocket connection attempt...")
            await asyncio.sleep(5)
        else:
             break # Exit if user stopped monitoring during error/cleanup

    print(f"Exiting subscribe_trader_activity task for user {user_id}")

# Main async function to manage the WebSocket thread
async def subscribe_vybe_trades(user_id: int, token_mint: str, fee_payer: str, context):
    api_key = os.getenv('API_KEY')
    websocket_uri = os.getenv('WS_URL', "wss://api.vybenetwork.xyz/live")

    if not api_key or not websocket_uri:
        print("API_KEY or WS_URL missing in .env")
        return

    print(f"Setting up WebSocket thread for user {user_id}, token {token_mint}, fee_payer {fee_payer}")

    # Get the current event loop *before* starting the thread
    main_loop = asyncio.get_running_loop()

    # Check if tracking a dev from the dev_trade_watchlist
    is_tracking_dev_trade = user_id in dev_trade_watchlists and fee_payer in dev_trade_watchlists[user_id]
    if is_tracking_dev_trade:
        print(f"Monitoring a developer from Dev Trade watchlist: {fee_payer}")

    while user_id in active_monitoring:
        ws_app = None
        ws_thread = None
        try:
            custom_headers = {"X-API-Key": api_key} # Format for websocket-client

            # Create WebSocketApp instance
            # Pass the captured main_loop to the on_message handler via lambda
            ws_app = websocket.WebSocketApp(
                websocket_uri,
                header=custom_headers,
                on_open=lambda ws: on_open(ws, token_mint, fee_payer),
                on_message=lambda ws, msg: on_message(ws, msg, user_id, token_mint, context, main_loop), # Pass main_loop
                on_error=on_error,
                on_close=on_close
            )

            # Start the WebSocket connection in a separate daemon thread
            # Daemon=True ensures the thread exits when the main program exits
            ws_thread = threading.Thread(target=ws_app.run_forever, daemon=True)
            print(f"Starting WebSocket thread {ws_thread.name}...")
            ws_thread.start()

            # Keep the async task alive while the thread is running and user is monitoring
            while (user_id in active_monitoring and ws_thread.is_alive() and 
                  (not is_tracking_dev_trade or fee_payer in dev_trade_watchlists.get(user_id, set()))):
                await asyncio.sleep(1) # Check every second

            # If we stopped because the dev was removed from watchlist
            if is_tracking_dev_trade and user_id in active_monitoring and ws_thread.is_alive() and fee_payer not in dev_trade_watchlists.get(user_id, set()):
                print(f"Developer {fee_payer} removed from Dev Trade watchlist, stopping monitoring")
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📊 Stopping monitoring for developer: `{fee_payer}` as they were removed from your Dev Trade watchlist",
                    parse_mode='Markdown'
                )
                if ws_app:
                    ws_app.close()
                break

            # If loop exits, either user stopped monitoring or thread died
            if not ws_thread.is_alive():
                print(f"WebSocket thread {ws_thread.name} died unexpectedly.")
                if user_id in active_monitoring:
                    print("Attempting to restart WebSocket thread...")
                else:
                    print("User stopped monitoring while thread was dead.")
            else: # User must have stopped monitoring
                 print(f"User {user_id} stopped monitoring. Shutting down WebSocket thread {ws_thread.name}...")
                 if ws_app: # Ensure ws_app exists before calling close
                    ws_app.close() # Gracefully close the connection
                 ws_thread.join(timeout=5) # Wait for thread to close
                 if ws_thread.is_alive():
                     print(f"Warning: WebSocket thread {ws_thread.name} did not terminate gracefully.")
                 break # Exit the outer while loop

        except Exception as e:
            print(f"Error setting up or managing WebSocket thread: {e}")
            # Ensure cleanup even on setup errors
            if ws_app:
                ws_app.close()
            if ws_thread and ws_thread.is_alive():
                ws_thread.join(timeout=1)

        # Wait before restarting the loop (if applicable)
        if user_id in active_monitoring:
            # Check if the dev is still in dev_trade_watchlist if applicable
            if is_tracking_dev_trade and fee_payer not in dev_trade_watchlists.get(user_id, set()):
                print(f"Developer {fee_payer} no longer in user's Dev Trade watchlist, stopping monitoring")
                break
            
            print("Waiting 5 seconds before restarting WebSocket connection attempt...")
            await asyncio.sleep(5)
        else:
             break # Exit if user stopped monitoring during error/cleanup

    print(f"Exiting subscribe_vybe_trades task for user {user_id}") 
