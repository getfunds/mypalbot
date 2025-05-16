"""
Command and callback handlers for the Telegram bot.
"""

import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Import from other modules
from state import user_watchlists, active_monitoring, trader_watchlists, active_trader_monitoring, pending_vybe_tracks, dev_trade_watchlists, trader_token_watchlists
from monitoring import subscribe_new_tokens, subscribe_trader_activity, subscribe_vybe_trades, subscribe_trader_token_activity

def get_monitoring_buttons(user_id: int) -> list:
    dev_button = InlineKeyboardButton(
        "✅ Dev Monitoring Active" if user_id in active_monitoring 
        else "👀🔍 Start Dev Monitoring", 
        callback_data="watch_dev"
    )
    trader_button = InlineKeyboardButton(
        "✅ Trader Monitoring Active" if user_id in active_trader_monitoring 
        else "👀👥 Start Trader Monitoring", 
        callback_data="watch_trader"
    )
    return [[dev_button]], [[trader_button]]

def get_home_page_markup(user_id: int) -> InlineKeyboardMarkup:
    """
    Create consistent home page keyboard markup for all return paths
    """
    dev_button, trader_button = get_monitoring_buttons(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton("🔍 Dev Tracking", callback_data="dev_tracking"),
            InlineKeyboardButton("👥 Trader Tracking", callback_data="trader_tracking")
        ],
        [*dev_button[0], *trader_button[0]],
        [
            InlineKeyboardButton("📋 My Watchlists", callback_data="show_watchlists")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def show_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE, is_query=False):
    """
    Displays the standardized home page
    """
    user_id = update.effective_user.id
    reply_markup = get_home_page_markup(user_id)
    
    welcome_text = (
        "👋 Welcome to MyPal, The fastest and simplest bot for tracking trader and developer wallets on Solana, using real-time monitoring data to remain ahead of the curve.\n\n"
        "Explore our wallet tracking features below. If you don't have a wallet to track, you can choose from <a href='https://vybe.fyi/wallets/top-traders'>this list of top traders</a>"
    )
    
    if is_query:
        # If coming from a callback query, delete the previous message and send a new one
        await update.callback_query.message.delete()
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        # If coming from a command, just reply to the message
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Initialize all watchlists if they don't exist
    if user_id not in user_watchlists:
        user_watchlists[user_id] = set()
    
    if user_id not in trader_watchlists:
        trader_watchlists[user_id] = set()
        
    if user_id not in dev_trade_watchlists:
        dev_trade_watchlists[user_id] = set()
        
    if user_id not in trader_token_watchlists:
        trader_token_watchlists[user_id] = {}
    
    await show_home_page(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    if query.data == "dev_tracking":
        keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Please enter the developer's address you want to track.\n"
            "Simply reply to this message with the address.",
            reply_markup=reply_markup
        )
        context.user_data['expecting_address'] = True
    
    elif query.data == "trader_tracking":
        keyboard = [
            [InlineKeyboardButton("👥 Track All Trades", callback_data="track_all_trades")],
            [InlineKeyboardButton("🎯 Track Specific Token", callback_data="track_specific_token")],
            [InlineKeyboardButton("🏠 Back to Home", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "How would you like to track a trader?",
            reply_markup=reply_markup
        )
    
    elif query.data == "track_all_trades":
        keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Please enter the trader's wallet address you want to track.\n"
            "Simply reply to this message with the address.",
            reply_markup=reply_markup
        )
        context.user_data['expecting_trader_address'] = True
    
    elif query.data == "track_specific_token":
        keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Please enter the trader's wallet address you want to track.\n"
            "Simply reply to this message with the address.",
            reply_markup=reply_markup
        )
        context.user_data['expecting_trader_token_address'] = True
    
    elif query.data == "show_watchlists":
        dev_list = "\n".join(f"• {addr}" for addr in user_watchlists.get(user_id, set())) or "Empty"
        trader_list = "\n".join(f"• {addr}" for addr in trader_watchlists.get(user_id, set())) or "Empty"
        
        # Add trader-token pairs if they exist
        trader_token_pairs = []
        if user_id in trader_token_watchlists:
            for trader, token in trader_token_watchlists[user_id].items():
                trader_token_pairs.append(f"• Trader: {trader}\n  Token: {token}")
        trader_token_list = "\n".join(trader_token_pairs) or "Empty"
        
        message = (
            "📋 Your Watchlists:\n\n"
            "🔍 Dev Watchlist:\n"
            f"{dev_list}\n\n"
            "👥 Trader Watchlist:\n"
            f"{trader_list}\n\n"
            "🎯 Trader-Token Watchlist:\n"
            f"{trader_token_list}\n\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("❌ Remove Address", callback_data="remove_address")],
            [InlineKeyboardButton("❌ Remove Trader-Token Pair", callback_data="remove_trader_token")],
            [InlineKeyboardButton("🏠 Back to Home", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    elif query.data == "start":
        await show_home_page(update, context, is_query=True)
    
    elif query.data == "list_addresses":
        if user_id not in user_watchlists or not user_watchlists[user_id]:
            keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Your watchlist is empty",
                reply_markup=reply_markup
            )
            return
        
        addresses = "\n".join(f"• {addr}" for addr in user_watchlists[user_id])
        keyboard = [
            [InlineKeyboardButton("❌ Remove Address", callback_data="remove_address")],
            [InlineKeyboardButton("🏠 Back to Home", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            f"Your watchlist:\n\n{addresses}",
            reply_markup=reply_markup
        )
    
    elif query.data == "remove_address":
        keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Please enter the address you want to remove from your watchlist.\n"
            "Simply reply to this message with the address.",
            reply_markup=reply_markup
        )
        context.user_data['expecting_remove_address'] = True
    
    elif query.data == "remove_trader_token":
        if user_id not in trader_token_watchlists or not trader_token_watchlists[user_id]:
            await query.message.reply_text("Your Trader-Token watchlist is empty")
            return
            
        keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Please enter the trader address for the pair you want to remove.\n"
            "Simply reply to this message with the address.",
            reply_markup=reply_markup
        )
        context.user_data['expecting_remove_trader_token'] = True
    
    elif query.data == "watch_dev":
        if user_id not in user_watchlists or not user_watchlists[user_id]:
            await query.message.reply_text("Please add developer addresses to your watchlist first!")
            return
        
        if user_id in active_monitoring:  
            active_monitoring.discard(user_id)
            await query.message.reply_text("❌ Developer monitoring stopped.")
        else:  
            active_monitoring.add(user_id)
            await query.message.reply_text("✅ Developer monitoring started!")
            asyncio.create_task(subscribe_new_tokens(user_id, context))
        
        # Update the home page buttons to reflect new state
        reply_markup = get_home_page_markup(user_id)
        await query.message.edit_reply_markup(reply_markup=reply_markup)

    elif query.data == "watch_trader":
        has_traders = user_id in trader_watchlists and trader_watchlists[user_id]
        has_trader_tokens = user_id in trader_token_watchlists and trader_token_watchlists[user_id]
        
        if not (has_traders or has_trader_tokens):
            await query.message.reply_text("Please add trader addresses to your watchlist first!")
            return
        
        if user_id in active_trader_monitoring:  
            active_trader_monitoring.discard(user_id)
            await query.message.reply_text("❌ Trader monitoring stopped.")
        else:  
            active_trader_monitoring.add(user_id)
            await query.message.reply_text("✅ Trader monitoring started!")
            
            # Start monitoring for general traders
            if has_traders:
                asyncio.create_task(subscribe_trader_activity(user_id, context))
            
            # Start monitoring for trader-token pairs
            if has_trader_tokens:
                for trader, token in trader_token_watchlists[user_id].items():
                    asyncio.create_task(subscribe_trader_token_activity(user_id, trader, token, context))
        
        # Update the home page buttons to reflect new state
        reply_markup = get_home_page_markup(user_id)
        await query.message.edit_reply_markup(reply_markup=reply_markup)

    elif query.data.startswith("track_dev_vybe:"):
        track_id = query.data.split(':')[1]
        lookup_key = f"{user_id}:{track_id}"
        track_info = pending_vybe_tracks.pop(lookup_key, None) # Retrieve and remove

        if track_info:
            token_mint = track_info['mint']
            fee_payer = track_info['dev'] # Get dev address stored as fee_payer

            try:
                print(f"Initiating Vybe tracking via button for token: {token_mint} and fee payer: {fee_payer}")
                # Decide which monitoring set to use. Using active_monitoring for now.
                # If you want separate control, create a new set e.g., active_vybe_monitoring.
                active_monitoring.add(user_id)
                
                # Add fee_payer to the dev_trade_watchlist
                if user_id not in dev_trade_watchlists:
                    dev_trade_watchlists[user_id] = set()
                dev_trade_watchlists[user_id].add(fee_payer)

                # Notify user
                await query.message.reply_text( # Send reply instead of editing original photo caption
                    f"✅ Starting Vybe monitoring for:\nToken: `{token_mint}`\nFee Payer (Dev): `{fee_payer}`",
                    parse_mode='Markdown'
                )

                # Start the Vybe monitoring task
                asyncio.create_task(subscribe_vybe_trades(user_id, token_mint, fee_payer, context))

            except Exception as e:
                 await query.message.reply_text(f"❌ Error starting Vybe monitoring: {e}")

        else:
            # Info expired or was invalid
            await query.answer("Tracking info not found or expired.", show_alert=True)
            # Optionally remove the button from the original message if possible/desired
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception as edit_error:
                print(f"Could not remove button after expiry: {edit_error}")

async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    expecting_dev = context.user_data.get('expecting_address', False)
    expecting_remove = context.user_data.get('expecting_remove_address', False)
    expecting_trader = context.user_data.get('expecting_trader_address', False)
    expecting_trader_token = context.user_data.get('expecting_trader_token_address', False)
    expecting_token_for_trader = context.user_data.get('expecting_token_for_trader', False)
    expecting_remove_trader_token = context.user_data.get('expecting_remove_trader_token', False)

    if not (expecting_dev or expecting_remove or expecting_trader or 
            expecting_trader_token or expecting_token_for_trader or expecting_remove_trader_token):
        return

    user_id = update.effective_user.id
    address = update.message.text.strip()
    
    if expecting_dev:
        if user_id not in user_watchlists:
            user_watchlists[user_id] = set()
        
        user_watchlists[user_id].add(address)
        
        keyboard = [
            [
                InlineKeyboardButton("🏠 Home", callback_data="start"),
                InlineKeyboardButton("➕ Add Another", callback_data="dev_tracking")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Address {address} has been added to your dev watchlist!",
            reply_markup=reply_markup
        )
        context.user_data['expecting_address'] = False
    
    elif expecting_remove:
        removed_from_dev = False
        removed_from_trader = False
        
        # Try to remove from both watchlists
        if user_id in user_watchlists and address in user_watchlists[user_id]:
            user_watchlists[user_id].remove(address)
            removed_from_dev = True
            
        if user_id in trader_watchlists and address in trader_watchlists[user_id]:
            trader_watchlists[user_id].remove(address)
            removed_from_trader = True
            
        if removed_from_dev or removed_from_trader:
            watchlist_type = ""
            if removed_from_dev:
                watchlist_type = "dev watchlist"
            if removed_from_trader:
                watchlist_type = "trader watchlist" if not removed_from_dev else "dev and trader watchlists"
                
            message = f"✅ Address {address} has been removed from your {watchlist_type}!"
        else:
            message = "❌ Address not found in your watchlists!"
        
        keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        context.user_data['expecting_remove_address'] = False
    
    elif expecting_trader:
        if user_id not in trader_watchlists:
            trader_watchlists[user_id] = set()
        
        trader_watchlists[user_id].add(address)
        
        # If trader monitoring is already active, start monitoring this new address immediately
        if user_id in active_trader_monitoring:
            asyncio.create_task(subscribe_trader_activity(user_id, context, specific_trader=address))
            monitoring_status = "✅ Trader address added and monitoring started automatically!"
        else:
            monitoring_status = "✅ Trader address added to your trader watchlist!"
            
        keyboard = [
            [
                InlineKeyboardButton("🏠 Home", callback_data="start"),
                InlineKeyboardButton("➕ Add Another", callback_data="track_all_trades")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{monitoring_status}\n"
            f"Trader: `{address}`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        context.user_data['expecting_trader_address'] = False
    
    elif expecting_trader_token:
        # Store the trader address and prompt for token address
        context.user_data['current_trader_address'] = address
        
        keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Trader address set: `{address}`\n\n"
            f"Now, please enter the Token Mint Address you want to track for this trader.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        context.user_data['expecting_trader_token_address'] = False
        context.user_data['expecting_token_for_trader'] = True
    
    elif expecting_token_for_trader:
        token_address = address
        trader_address = context.user_data.get('current_trader_address')
        
        if not trader_address:
            await update.message.reply_text("❌ Error: Trader address was not found. Please start over.")
            context.user_data['expecting_token_for_trader'] = False
            return
        
        # Initialize trader_token_watchlists for the user if needed
        if user_id not in trader_token_watchlists:
            trader_token_watchlists[user_id] = {}
        
        # Store the trader-token pair
        trader_token_watchlists[user_id][trader_address] = token_address
        
        # If trader monitoring is already active, start monitoring this new trader-token pair immediately
        if user_id in active_trader_monitoring:
            asyncio.create_task(subscribe_trader_token_activity(user_id, trader_address, token_address, context))
            monitoring_status = "✅ Trader-token pair added and monitoring started automatically!"
        else:
            monitoring_status = "✅ Trader-token pair added to your watchlist!"
        
        keyboard = [
            [
                InlineKeyboardButton("🏠 Home", callback_data="start"),
                InlineKeyboardButton("➕ Add Another", callback_data="track_specific_token")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{monitoring_status}\n\n"
            f"Trader: `{trader_address}`\n"
            f"Token: `{token_address}`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        context.user_data['expecting_token_for_trader'] = False
        context.user_data.pop('current_trader_address', None)
    
    elif expecting_remove_trader_token:
        trader_address = address
        
        if user_id in trader_token_watchlists and trader_address in trader_token_watchlists[user_id]:
            token = trader_token_watchlists[user_id][trader_address]
            del trader_token_watchlists[user_id][trader_address]
            message = f"✅ Trader-Token pair removed!\nTrader: `{trader_address}`\nToken: `{token}`"
        else:
            message = "❌ Trader address not found in your Trader-Token watchlist!"
        
        keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        context.user_data['expecting_remove_trader_token'] = False

async def add_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Please provide an address to add")
        return
    
    address = context.args[0]
    if user_id not in user_watchlists:
        user_watchlists[user_id] = set()
    
    user_watchlists[user_id].add(address)
    await update.message.reply_text(f"Address {address} added to your watchlist")

async def remove_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Please provide an address to remove")
        return
    
    address = context.args[0]
    if user_id in user_watchlists and address in user_watchlists[user_id]:
        user_watchlists[user_id].remove(address)
        await update.message.reply_text(f"Address {address} removed from your watchlist")
    else:
        await update.message.reply_text("Address not found in your watchlist")

async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command handler for /home - takes the user back to the home page
    """
    await show_home_page(update, context)

async def list_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_watchlists or not user_watchlists[user_id]:
        await update.message.reply_text("Your watchlist is empty")
        return
    
    addresses = "\n".join(user_watchlists[user_id])
    await update.message.reply_text(f"Your watchlist:\n{addresses}") 
