# ⚡ AlphaStream: Real-Time Statistical Arbitrage Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

APP URL - https://gemscap-aplhastream-startarb-engine.streamlit.app/

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


project/
│── app.py             # Frontend entry point (Streamlit)
│── ingest.py          # WebSocket client for data ingestion
│── analytics.py       # Core Math logic (OLS, Kalman, Backtest)
│── storage.py         # Thread-safe database & memory buffer
│── config.py          # Configuration constants
│── requirements.txt   # Python dependencies
│── README.md          # Documentation
└── architecture.png   # System architecture diagram


🛠️ Setup & Execution

Prerequisites

Python 3.8+

Virtual Environment (Recommended)

Installation

Clone the repository:

git clone [https://github.com/YOUR_USERNAME/AlphaStream.git](https://github.com/YOUR_USERNAME/AlphaStream.git)
cd AlphaStream


Install Dependencies:

pip install -r requirements.txt


Running Locally

Execute the single-command entry point:

streamlit run app.py


The dashboard will open automatically in your default browser at http://localhost:8501.

☁️ Deployment Guide

This application is optimized for Streamlit Community Cloud.

Push to GitHub: Ensure your code is in a public GitHub repository.

Connect Streamlit:

Go to share.streamlit.io.

Click "New App".

Select your repository (AlphaStream) and branch (main).

Path to main file: app.py.

Deploy: Click "Deploy". The build process will install dependencies from requirements.txt and launch the app.

Configuration: No secrets are required as the app uses public Binance APIs.

🧮 Methodology

The core strategy implements a Pairs Trading (Statistical Arbitrage) logic:

Data Alignment: High-frequency ticks are aligned via forward-filling (ffill) to ensure synchronous timestamps between Asset X (Independent) and Asset Y (Dependent).

Hedge Ratio ($\beta$): Calculated via a Rolling Window ($N=20...500$).

Equation: $Spread_t = PriceY_t - (\beta_t \cdot PriceX_t + \alpha_t)$

Normalization: $ZScore_t = \frac{Spread_t - \mu_{spread}}{\sigma_{spread}}$

Signal Generation:

Short Spread: When $Z > Threshold$ (Asset Y is overvalued relative to X).

Long Spread: When $Z < -Threshold$ (Asset Y is undervalued relative to X).

🤖 AI Usage Transparency

Tools Used: Gemini Pro (Architecture), ChatGPT (Debugging), Claude (Review).

Usage Scope:

Boilerplate: Generated initial Plotly chart configurations to accelerate UI development.

Math Validation: Verified matrix dimensions for the vectorized Kalman Filter update step.

Debugging: Resolved KeyError issues in CSV uploads by suggesting robust column normalization (stripping whitespace, mapping aliases).

Human Intervention:

System Architecture: Designed the threaded Producer-Consumer pattern.

Analytic Selection: Chose Robust Regression (Huber) specifically to counter crypto volatility "wicks".

UX Design: Implemented the "Progressive Loading" state to improve user experience during data buffering.

Prompt given to Gemini:

You are a Senior Quantitative Developer, Systems Architect, and Full-Stack Engineer working at a top multi-factor trading firm (stat-arb, market-making, risk-premia).
Your task is to design, implement, and document an end-to-end Real-Time Statistical Arbitrage Analytics Dashboard that fully satisfies the following Quant Developer Evaluation Assignment.

🔴 HARD REQUIREMENTS (DO NOT SKIP)
You must:

Build a complete runnable application
Provide all source code
Explain architecture & design choices
Include bonus/advanced features for brownie points
Ensure correctness, modularity, and clarity
Use Python for backend
Single-command execution (python app.py)
Works with REAL Binance WebSocket data (no dummy dependency)
📂 PROJECT SCOPE
1️⃣ Data Ingestion
Consume real-time Binance Futures WebSocket trade stream
Use fields: {timestamp, symbol, price, size}
Support multiple symbols simultaneously
Decouple ingestion from analytics
Handle reconnects & failures gracefully
2️⃣ Storage Layer
Store tick data efficiently
Support:
Raw tick storage
Resampled data: 1s, 1m, 5m
Choose appropriate local storage (SQLite / in-memory + persistence)
Explain trade-offs clearly
3️⃣ Analytics Engine (MANDATORY)
Implement correct, numerically sound versions of:

Price statistics (mean, variance, returns)
Hedge ratio via OLS regression
Spread calculation
Z-score (rolling window)
ADF stationarity test
Rolling correlation
Volume analytics
4️⃣ Live Analytics
Live updating stats (≤500ms latency)
Different refresh cadences:
Tick-level metrics: live
1m / 5m charts: update on resample boundary
Clearly explain how this is handled
5️⃣ Frontend Dashboard
Use Streamlit (preferred) or Dash
Interactive controls:
Symbol selection
Timeframe (1s / 1m / 5m)
Rolling window
Regression type
Trigger ADF test
Charts:
Price series
Spread
Z-score
Correlation
Volume
Charts must support zoom, pan, hover
Multi-asset analytics visible simultaneously
6️⃣ Alerting System
Rule-based alerts (e.g., z-score > 2)
Configurable from UI
Real-time alert display
7️⃣ Data Export
Download processed analytics as CSV
Download resampled datasets
⭐ BONUS (VERY IMPORTANT – brownie points)
You MUST include:

Kalman Filter dynamic hedge ratio
Mini mean-reversion backtest:
Entry: |z| > 2
Exit: z → 0
Table of rolling stats by minute (exportable)
Thoughtful visual summaries (heatmap / stats table)
Clean extensible module structure
🧠 ARCHITECTURE EXPECTATIONS
Design with future scaling in mind:

Loosely coupled components:
ingestion
storage
analytics
alerts
frontend
Ability to swap data source (CME / REST / CSV) with minimal changes
Clear interfaces
Explain scaling pain points and mitigations
📁 DELIVERABLES YOU MUST OUTPUT
1️⃣ Folder Structure
Provide a clean project layout, e.g.

project/
│── app.py
│── ingest/
│── analytics/
│── storage/
│── alerts/
│── utils/
│── requirements.txt
│── README.md
│── architecture.drawio
│── architecture.png
2️⃣ Complete Source Code
Every file fully written
No pseudocode
Production-quality readability
3️⃣ README.md
Must include:

Setup instructions
How to run
Analytics explanation
Design decisions
Scaling discussion
4️⃣ Architecture Diagram
Explain components & data flow
Provide both:
.drawio source
exported PNG/SVG
5️⃣ ChatGPT / AI Usage Note
Short transparency note:
What AI helped with
What decisions were human-driven
6️⃣ Deployment
Provide free deployment option:
Streamlit Community Cloud or equivalent
Step-by-step deployment guide
🧪 QUALITY BAR
Assume this is reviewed by senior quant researchers
Analytics correctness > fancy UI
Clear reasoning > over-engineering
No hidden dependencies
No broken imports
No fake data
Everything must run
🎯 FINAL OUTPUT FORMAT
Deliver your response in the following order:

High-level system overview
Architecture diagram explanation
Complete project folder structure
Full source code (file-by-file)
README.md
Deployment guide
AI usage transparency note
What brownie points this implementation achieves
Act like this is a real take-home assignment for a Quant Developer role and aim to maximize evaluation score across frontend, backend, and architecture.
Do not ask follow-up questions.
Make reasonable assumptions and state them clearly.

Submitted for Quant Developer Evaluation.
