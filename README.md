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

Tools Used: ChatGPT (GPT-4o / Claude 3.5 Sonnet equivalent)

Usage Scope:

Boilerplate Generation: Used for setting up the initial Streamlit layout and Plotly chart configurations to save time on CSS/UI styling.

Mathematical Validation: Verified the vectorized implementation of the Kalman Filter update step to ensure matrix dimensions were correct for a 1D price series.

Debugging: Assisted in resolving KeyError issues during CSV uploads by suggesting robust column normalization techniques (stripping whitespace, mapping aliases).

Human Intervention:

System Architecture design (Producer-Consumer pattern).

Selection of Robust Regression (Huber) as a specific counter to crypto price spikes.

Logic for the "Progressive Loading" state to improve UX.

📂 File Structure

app.py: Frontend entry point (Streamlit).

analytics.py: Pure math logic (StatArb models, Backtesting).

ingest.py: Async WebSocket client for Binance.

storage.py: Thread-safe In-Memory + SQLite storage engine.

config.py: Centralized configuration constants.
