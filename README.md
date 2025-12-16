⚡ AlphaStream: Real-Time Statistical Arbitrage Engine

A production-grade Quantitative Analytics dashboard designed to ingest real-time Binance Futures data, calculate co-integration metrics (Spread, Z-Score, Beta) on the fly, and visualize arbitrage opportunities.

📋 Project Overview

This application serves as a prototype for an end-to-end quantitative trading monitor. It features a loosely coupled architecture separating data ingestion (WebSocket) from computation (Analytics Engine) and visualization (Streamlit).

Key Features

Multi-Mode Ingestion:

Live: Consumes real-time aggTrade streams from Binance Futures.

Historical: Upload CSV files for backtesting and analysis.

Advanced Analytics:

OLS (Ordinary Least Squares): Standard static hedge ratio estimation.

Kalman Filter: Dynamic, adaptive beta estimation for volatile regimes.

Robust Regression: Huber-loss based rolling regression to ignore outliers.

Market Microstructure: Real-time liquidity/volume profile monitoring.

Risk Management: Automated stationarity tests (ADF) and Z-Score alerting.

🛠️ Setup & Execution

Prerequisites

Python 3.8+

Virtual Environment (Recommended)

Installation

Clone/Unzip the project folder.

Install Dependencies:

pip install -r requirements.txt


(Requires: streamlit, pandas, numpy, plotly, websocket-client, statsmodels, scipy)

Running the App

Execute the following single command in your terminal:

streamlit run app.py


🧠 Methodology & Analytics

The core strategy is a Pairs Trading (Statistical Arbitrage) approach:

Data Alignment: High-frequency ticks are aligned via forward-filling to ensure synchronous timestamps between Asset X (Independent) and Asset Y (Dependent).

Hedge Ratio ($\beta$): Calculated via a Rolling Window ($N=20...500$).

$Spread_t = PriceY_t - (\beta_t \cdot PriceX_t + \alpha_t)$

$ZScore_t = \frac{Spread_t - \mu_{spread}}{\sigma_{spread}}$

Signal Generation:

Short Spread: When $Z > Threshold$ (Asset Y is overvalued relative to X).

Long Spread: When $Z < -Threshold$ (Asset Y is undervalued relative to X).

🤖 AI Usage Transparency

Tools Used: Gemini Pro for code building, ChatGPT for debugging and Claude for review

Usage Scope:

Boilerplate Generation: Used for setting up the initial Streamlit layout and Plotly chart configurations to save time on CSS/UI styling.

Mathematical Validation: Verified the vectorized implementation of the Kalman Filter update step to ensure matrix dimensions were correct for a 1D price series.

Debugging: Assisted in resolving KeyError issues during CSV uploads by suggesting robust column normalization techniques (stripping whitespace, mapping aliases).

Human Intervention:

System Architecture design (Producer-Consumer pattern).

Selection of Robust Regression (Huber) as a specific counter to crypto price spikes.

Logic for the "Progressive Loading" state to improve UX.

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

📂 File Structure

app.py: Frontend entry point (Streamlit).

analytics.py: Pure math logic (StatArb models, Backtesting).

ingest.py: Async WebSocket client for Binance.

storage.py: Thread-safe In-Memory + SQLite storage engine.

config.py: Centralized configuration constants.
