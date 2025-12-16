# ⚡ AlphaStream: Real-Time Statistical Arbitrage Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

**AlphaStream** is a production-grade Quantitative Analytics dashboard designed to ingest real-time Binance Futures data, calculate co-integration metrics (Spread, Z-Score, Beta) on the fly, and visualize arbitrage opportunities.

This application serves as a prototype for an end-to-end quantitative trading monitor, featuring a loosely coupled architecture that separates data ingestion (WebSocket) from computation (Analytics Engine) and visualization (Streamlit).

---

## 🚀 Key Features

### 📡 Multi-Mode Ingestion
* **Live Stream**: Consumes real-time `aggTrade` streams from Binance Futures via WebSocket.
* **Historical Mode**: Upload CSV files (OHLCV or tick data) for backtesting and static analysis.

### 🧠 Advanced Analytics (Quant Engine)
* **OLS (Ordinary Least Squares)**: Standard static hedge ratio estimation.
* **Kalman Filter (Bonus)**: Dynamic, adaptive beta estimation for volatile regimes.
* **Robust Regression (Bonus)**: Huber-loss based rolling regression to mitigate the impact of price outliers.
* **Market Microstructure**: Real-time liquidity and volume profile monitoring.
* **Risk Management**: Automated stationarity tests (ADF) and Z-Score alerting.

### 📊 Interactive Dashboard
* **Real-time Visualization**: Dynamic Plotly charts updating <500ms latency.
* **Progressive Loading**: Immediate price rendering while statistical models calibrate.
* **Trader Tools**: Configurable lookback windows, Z-score thresholds, and alert triggers.
* **Data Export**: Download processed analytics and resampled datasets as CSV.

---

## 🏗️ Architecture & Design

### High-Level Overview
The system follows a **Producer-Consumer** pattern decoupled by a thread-safe storage layer.

![Architecture Diagram](architecture.png)

1.  **Ingest Service (Producer)**: A background daemon thread connects to Binance WebSockets, normalizing raw JSON ticks into structured data.
2.  **Storage Layer (Buffer)**: 
    * **Hot Path**: `deque` ring-buffer for O(1) recent access (critical for live analytics).
    * **Persistence**: Asynchronous writes to SQLite (WAL mode) for historical resampling.
3.  **Quant Engine (Consumer)**: Vectorized pandas/numpy operations compute rolling statistics on the "Hot Path" data.
4.  **Frontend (UI)**: Streamlit polls the storage layer, triggering the Quant Engine only when new data renders.

### Design Decisions & Trade-offs
* **Streamlit vs. React**: Streamlit was chosen for rapid prototyping and Python-native integration, allowing us to focus on analytics correctness. **Trade-off**: Lower UI customizability compared to React/Dash.
* **SQLite vs. TimeSeriesDB**: SQLite is serverless and sufficient for single-day high-frequency data. **Trade-off**: For multi-day, terabyte-scale storage, this would be replaced by KDB+ or TimescaleDB.
* **Hybrid Storage**: We use in-memory buffers for calculation speed and disk storage for safety. This minimizes I/O latency during the critical rendering loop.

### Scaling Discussion
If this were to move to a firm-wide production environment, the following changes would be made:
1.  **Ingestion**: Move `ingest.py` to a separate microservice publishing to a low-latency bus (e.g., **Kafka** or **Redpanda**).
2.  **Storage**: Replace SQLite with **KDB+** or **QuestDB** to handle billions of ticks efficiently.
3.  **Compute**: Offload heavy math (Kalman Filters) to a compiled backend (C++/Rust) exposed via Python bindings.

---

## 📂 Project Structure

```text
project/
│── app.py             # Frontend entry point (Streamlit)
│── ingest.py          # WebSocket client for data ingestion
│── analytics.py       # Core Math logic (OLS, Kalman, Backtest)
│── storage.py         # Thread-safe database & memory buffer
│── config.py          # Configuration constants
│── requirements.txt   # Python dependencies
│── README.md          # Documentation
└── architecture.png   # System architecture diagram

🛠️ Setup & ExecutionPrerequisitesPython 3.8+Virtual Environment (Recommended)InstallationClone the repository:Bashgit clone [https://github.com/YOUR_USERNAME/AlphaStream.git](https://github.com/YOUR_USERNAME/AlphaStream.git)
cd AlphaStream
Install Dependencies:Bashpip install -r requirements.txt
Running LocallyExecute the single-command entry point:Bashstreamlit run app.py
The dashboard will open automatically in your default browser at http://localhost:8501.☁️ Deployment GuideThis application is optimized for Streamlit Community Cloud.Push to GitHub: Ensure your code is in a public GitHub repository.Connect Streamlit:Go to share.streamlit.io.Click "New App".Select your repository (AlphaStream) and branch (main).Path to main file: app.py.Deploy: Click "Deploy". The build process will install dependencies from requirements.txt and launch the app.Configuration: No secrets are required as the app uses public Binance APIs.🧮 MethodologyThe core strategy implements a Pairs Trading (Statistical Arbitrage) logic:Data Alignment: High-frequency ticks are aligned via forward-filling (ffill) to ensure synchronous timestamps between Asset X (Independent) and Asset Y (Dependent).Hedge Ratio ($\beta$): Calculated via a Rolling Window ($N=20...500$).Equation: $Spread_t = PriceY_t - (\beta_t \cdot PriceX_t + \alpha_t)$Normalization: $ZScore_t = \frac{Spread_t - \mu_{spread}}{\sigma_{spread}}$Signal Generation:Short Spread: When $Z > Threshold$ (Asset Y is overvalued relative to X).Long Spread: When $Z < -Threshold$ (Asset Y is undervalued relative to X).🤖 AI Usage TransparencyTools Used: Gemini Pro (Architecture), ChatGPT (Debugging), Claude (Review).Usage Scope:Boilerplate: Generated initial Plotly chart configurations to accelerate UI development.Math Validation: Verified matrix dimensions for the vectorized Kalman Filter update step.Debugging: Resolved KeyError issues in CSV uploads by suggesting robust column normalization (stripping whitespace, mapping aliases).Human Intervention:System Architecture: Designed the threaded Producer-Consumer pattern.Analytic Selection: Chose Robust Regression (Huber) specifically to counter crypto volatility "wicks".UX Design: Implemented the "Progressive Loading" state to improve user experience during data buffering.Submitted for Quant Developer Evaluation.
