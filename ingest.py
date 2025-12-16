import websocket
import json
import threading
import time
from datetime import datetime
import config

class BinanceStreamer(threading.Thread):
    """
    Dedicated Background Thread for Data Ingestion.
    Connects to Binance Futures WebSocket, parses data, pushes to Store.
    """
    
    def __init__(self, store, symbols=config.SYMBOLS):
        super().__init__()
        self.store = store
        self.symbols = [s.lower() for s in symbols]
        self.ws = None
        self.keep_running = True
        self.daemon = True  # Killed when main process exits

    def _get_stream_url(self):
        # Format: btcusdt@aggTrade/ethusdt@aggTrade
        streams = "/".join([f"{s}@aggTrade" for s in self.symbols])
        return f"{config.BINANCE_WS_URL}{streams}"

    def on_message(self, ws, message):
        """
        Binance AggTrade Format:
        {
          "e": "aggTrade",  // Event type
          "E": 123456789,   // Event time
          "s": "BTCUSDT",   // Symbol
          "p": "0.001",     // Price
          "q": "100",       // Quantity
          ...
        }
        """
        try:
            data = json.loads(message)
            if 'data' in data:
                payload = data['data']
                tick = {
                    'timestamp': payload['E'] / 1000.0, # Convert ms to seconds
                    'symbol': payload['s'],
                    'price': float(payload['p']),
                    'size': float(payload['q'])
                }
                self.store.save_tick(tick)
        except Exception as e:
            print(f"[WS Error] Parse failed: {e}")

    def on_error(self, ws, error):
        print(f"[WS Error] {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("[WS] Closed")

    def on_open(self, ws):
        print("[WS] Connected to Binance Futures")

    def run(self):
        while self.keep_running:
            try:
                url = self._get_stream_url()
                print(f"[WS] Connecting to {url}...")
                self.ws = websocket.WebSocketApp(
                    url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever()
            except Exception as e:
                print(f"[WS] Connection failed: {e}. Retrying in 5s...")
                time.sleep(5)

    def stop(self):
        self.keep_running = False
        if self.ws:
            self.ws.close()
