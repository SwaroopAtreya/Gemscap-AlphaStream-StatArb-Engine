import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from collections import deque
from threading import Lock
import config

class TradeStore:
    """
    Hybrid Storage Engine:
    1. In-Memory Deque (Ring Buffer) for O(1) recent access (Critical for Live Analytics).
    2. SQLite for persistent historical storage and resampling.
    """
    
    def __init__(self, db_name=config.DB_NAME, symbols=config.SYMBOLS):
        self.db_name = db_name
        self.symbols = symbols
        self.lock = Lock()
        
        # In-memory fast buffer: {symbol: deque([...])}
        self.memory_buffer = {
            sym: deque(maxlen=config.MEMORY_BUFFER_SIZE) 
            for sym in symbols
        }
        
        self._init_db()

    def _init_db(self):
        """Initialize SQLite with WAL mode for better concurrency."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Optimize SQLite for write-heavy workloads
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                timestamp REAL,
                symbol TEXT,
                price REAL,
                size REAL,
                PRIMARY KEY (timestamp, symbol)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ts ON trades(timestamp)")
        conn.commit()
        conn.close()

    def save_tick(self, tick_data: dict):
        """
        Thread-safe write to both Memory and Disk.
        tick_data expected format: {'timestamp': float, 'symbol': str, 'price': float, 'size': float}
        """
        with self.lock:
            # 1. Write to Memory
            self.memory_buffer[tick_data['symbol']].append(tick_data)
        
        # 2. Write to Disk (In a real system, this would be batched/async)
        try:
            conn = sqlite3.connect(self.db_name)
            conn.execute(
                "INSERT OR IGNORE INTO trades (timestamp, symbol, price, size) VALUES (?, ?, ?, ?)",
                (tick_data['timestamp'], tick_data['symbol'], tick_data['price'], tick_data['size'])
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Storage Error] {e}")

    def get_recent_ticks(self, limit=1000) -> pd.DataFrame:
        """Fetch raw ticks from memory buffer (Fastest)."""
        all_data = []
        with self.lock:
            for sym in self.symbols:
                # Convert deque to list
                data = list(self.memory_buffer[sym])
                if data:
                    all_data.extend(data)
        
        if not all_data:
            return pd.DataFrame(columns=['timestamp', 'symbol', 'price', 'size'])

        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df.sort_values('timestamp')

    def get_resampled_data(self, interval='1min', limit=1000) -> pd.DataFrame:
        """
        Fetch historical data from SQLite and resample.
        Used for 1m/5m charts.
        """
        conn = sqlite3.connect(self.db_name)
        # Fetch raw data roughly covering the needed interval
        # Simplified query: fetch last N rows (production would use time range)
        query = f"SELECT timestamp, symbol, price FROM trades ORDER BY timestamp DESC LIMIT {limit * 10}"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            return pd.DataFrame()

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        
        # Pivot to wide format for easier resampling: Columns [BTCUSDT, ETHUSDT]
        pivot_df = df.pivot(columns='symbol', values='price')
        
        # Resample logic (OHLC or close)
        resampled = pivot_df.resample(interval).ffill().dropna()
        return resampled.tail(limit)

    def clear_db(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("DELETE FROM trades")
        conn.commit()
        conn.close()
