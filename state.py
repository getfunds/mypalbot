"""
Global state variables and data structures used throughout the bot.
"""

# User watchlists for monitoring developers
user_watchlists = {}

# Set of active monitoring user IDs 
active_monitoring = set()

# User watchlists for monitoring traders
trader_watchlists = {}

# Set of active trader monitoring user IDs
active_trader_monitoring = set()

# Dictionary to store pending Vybe tracks keyed by user_id:track_id
pending_vybe_tracks = {} 

# User watchlists for monitoring dev trades (separate from regular dev watchlist)
dev_trade_watchlists = {}

# Map of user_id → dictionary of trader_address → token_address
trader_token_watchlists = {} 