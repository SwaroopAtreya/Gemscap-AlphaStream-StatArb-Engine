# Real-Time Statistical Arbitrage Analytics Dashboard

A production-grade Quantitative Analytics dashboard designed to ingest real-time Binance Futures data, calculate co-integration metrics (Spread, Z-Score, Beta) on the fly, and visualize arbitrage opportunities.

## 🚀 Key Features

* **Real-Time Ingestion**: Asynchronous background thread consuming Binance WebSocket `aggTrade` streams.
* **Hybrid Storage**: `deque` ring-buffer for sub-millisecond hot-path access + `SQLite WAL` for persistence.
* **Quant Analytics Engine**:
    * **Rolling OLS**: Standard hedge ratio calculation.
    * **Kalman Filter (Bonus)**: Dynamic state-space beta estimation.
    * **ADF Test**: On-demand stationarity verification.
    * **Backtest Engine**: Vectorized historical simulation of the current session.
* **Interactive UI**: Built with Streamlit & Plotly.

## 🛠️ Installation & Setup

1.  **Environment Setup**:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Run Application**:
    ```bash
    streamlit run app.py
    ```

3.  **Usage**:
    * The dashboard will auto-connect to Binance.
    * Wait ~5 seconds for the initial buffer to fill.
    * Toggle between **OLS** and **Kalman Filter** in the sidebar to see how the Hedge Ratio adapts.
