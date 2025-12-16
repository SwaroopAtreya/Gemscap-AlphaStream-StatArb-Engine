import os

# --- Data Source Config ---
BINANCE_WS_URL = "wss://fstream.binance.com/stream?streams="
# Default StatArb Pair: ETH vs BTC
SYMBOLS = ["BTCUSDT", "ETHUSDT"] 

# --- Storage Config ---
DB_NAME = "tick_store.db"
# Keep last N ticks in memory for high-speed calculation
MEMORY_BUFFER_SIZE = 2000 

# --- Analytics Config ---
DEFAULT_LOOKBACK_WINDOW = 100
DEFAULT_Z_THRESHOLD = 2.0
RISK_FREE_RATE = 0.0

# --- Visualization ---
REFRESH_RATE_MS = 1000  # Dashboard refresh rate
