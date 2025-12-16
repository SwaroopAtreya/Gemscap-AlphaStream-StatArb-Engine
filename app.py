import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime

# Internal imports
import config
from storage import TradeStore
from ingest import BinanceStreamer
from analytics import QuantEngine

# --- 1. PRO UI CONFIGURATION ---
st.set_page_config(
    page_title="AlphaStream | StatArb Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (The "Pro" Look) ---
st.markdown("""
<style>
    /* Global Reset & Font */
    .block-container {
        padding-top: 5rem;      /* INCREASED to pull content down */
        padding-bottom: 5rem;   /* Added bottom padding */
        padding-left: 2rem;     
        padding-right: 2rem;
    }
    
    /* Card Styling for Metrics */
    div[data-testid="stMetric"] {
        background-color: #1a1c24; /* Darker card background */
        border: 1px solid #2d303e;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
        min-height: 80px;      /* Compact height */
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #4a4d5e;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0e1117;
        border-right: 1px solid #2d303e;
    }
    
    /* Custom Alert Boxes */
    .trade-signal-box {
        padding: 10px;          
        border-radius: 8px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        border: 1px solid rgba(255,255,255,0.1);
        height: 100%;           
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .signal-long {
        background: linear-gradient(135deg, #052c65 0%, #004d40 100%);
        border-left: 5px solid #00e676;
    }
    .signal-short {
        background: linear-gradient(135deg, #4a0000 0%, #8b0000 100%);
        border-left: 5px solid #ff1744;
    }
    .signal-neutral {
        background-color: #1a1c24;
        border-left: 5px solid #757575;
        color: #b0b0b0;
    }
    
    /* Text Typography */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .big-signal-text {
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: 1px;
        color: #ffffff;
    }
    .sub-signal-text {
        font-size: 0.85rem;
        opacity: 0.8;
        color: #e0e0e0;
    }
    
    /* Chart Container */
    .stPlotlyChart {
        background-color: #1a1c24;
        border-radius: 8px;
        border: 1px solid #2d303e;
        padding: 10px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SINGLETON INITIALIZATION ---
@st.cache_resource
def get_system_components():
    store = TradeStore()
    streamer = BinanceStreamer(store)
    streamer.start()
    return store, streamer

store, streamer = get_system_components()

# --- 4. SIDEBAR CONTROLS & HEALTH ---
with st.sidebar:
    st.title("⚡ AlphaStream")
    
    # --- NEW: Data Source Selection ---
    st.markdown("### 📡 Data Source")
    data_source = st.radio("Mode", ["Live Stream", "Historical Upload"], horizontal=True, label_visibility="collapsed")
    
    uploaded_file = None
    if data_source == "Historical Upload":
        uploaded_file = st.file_uploader("Upload Ticks CSV", type=['csv'], help="Columns: timestamp, symbol, price, size")
        auto_refresh = False
        st.info("Live ingestion paused.")
    else:
        # Status Indicator
        ticks_in_mem = len(store.memory_buffer[config.SYMBOLS[0]])
        buffer_pct = min(ticks_in_mem / config.MEMORY_BUFFER_SIZE, 1.0)
        
        status_color = "green" if buffer_pct > 0.1 else "orange" if buffer_pct > 0 else "red"
        st.markdown(f"**System Status**: :{status_color}[●] Connected")
        
        st.progress(buffer_pct)
        st.caption(f"Buffer: {ticks_in_mem}/{config.MEMORY_BUFFER_SIZE} ticks")
        auto_refresh = st.toggle("Live Polling (1s)", value=True)
    
    st.divider()
    
    with st.expander("⚙️ Strategy Config", expanded=True):
        sym_y = st.selectbox("Y (Dependent)", config.SYMBOLS, index=1)
        sym_x = st.selectbox("X (Independent)", config.SYMBOLS, index=0)
        
        window = st.slider("Lookback Window", 20, 500, config.DEFAULT_LOOKBACK_WINDOW)
        z_thresh = st.slider("Z-Score Entry", 1.0, 4.0, config.DEFAULT_Z_THRESHOLD)
        exit_thresh = st.slider("Z-Score Exit", 0.0, 1.0, 0.0)
        
        # Added Robust Option
        calc_method = st.radio("Model", ["OLS (Static)", "Kalman (Dynamic)", "Robust (Huber)"], horizontal=False)

# --- 5. DATA INGESTION & ANALYTICS ---

# Handle Data Source
if data_source == "Historical Upload" and uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
        if 'timestamp' in raw_df.columns:
            raw_df['timestamp'] = pd.to_datetime(raw_df['timestamp'])
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()
else:
    raw_df = store.get_recent_ticks()

df_aligned = QuantEngine.prepare_aligned_data(raw_df, sym_x, sym_y)

# --- LOADING STATE ---
if df_aligned.empty:
    if data_source == "Live Stream":
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("### 🚀 Initializing Strategy Engine...")
            st.info(f"Gathering sufficient market data...")
        time.sleep(1)
        if auto_refresh: st.rerun()
        st.stop()
    else:
        st.info("Please upload a CSV file.")
        st.stop()

# Method Selection
if "Kalman" in calc_method: method_key = "Kalman"
elif "Robust" in calc_method: method_key = "Robust (Huber)"
else: method_key = "OLS"

# Run Calculation
analytics_df = QuantEngine.calculate_metrics(df_aligned, window, method_key)

# --- 6. KPI DASHBOARD ---
# Check if calibration is complete (Z-score exists and not NaN)
is_calibrated = 'z_score' in analytics_df.columns and not analytics_df['z_score'].iloc[-1:].isna().all()

if is_calibrated:
    try:
        last_row = analytics_df.iloc[-1]
        curr_z = last_row['z_score']
        curr_spread = last_row['spread']
        curr_beta = last_row['beta']
        
        raw_corr = analytics_df['x'].rolling(window).corr(analytics_df['y']).iloc[-1]
        curr_corr = 0.0 if np.isnan(raw_corr) else raw_corr
        
        prev_z = analytics_df['z_score'].iloc[-2] if len(analytics_df) > 1 else curr_z
        z_delta = curr_z - prev_z

        # Signal Logic
        if curr_z > z_thresh:
            sig_cls, sig_ico, sig_txt, sig_sub = "trade-signal-box signal-short", "⬇️", f"SHORT {sym_y}", f"Z ({curr_z:.2f}) > {z_thresh}"
        elif curr_z < -z_thresh:
            sig_cls, sig_ico, sig_txt, sig_sub = "trade-signal-box signal-long", "⬆️", f"LONG {sym_y}", f"Z ({curr_z:.2f}) < -{z_thresh}"
        else:
            sig_cls, sig_ico, sig_txt, sig_sub = "trade-signal-box signal-neutral", "⏸️", "NO SIGNAL", f"Z ({curr_z:.2f}) in range"
            
    except Exception as e:
        is_calibrated = False
else:
    # Calibrating State
    curr_z, curr_spread, curr_beta, curr_corr, z_delta = 0.0, 0.0, 0.0, 0.0, 0.0
    sig_cls, sig_ico, sig_txt, sig_sub = "trade-signal-box signal-neutral", "⏳", "CALIBRATING", f"Need {window - len(df_aligned)} more ticks"

# Layout: 2 Columns (Signal Left, Metrics Right)
col_signal, col_kpi = st.columns([1.5, 3.5])

with col_signal:
    st.markdown(f"""
        <div class="{sig_cls}">
            <div class="big-signal-text">{sig_ico} {sig_txt}</div>
            <div class="sub-signal-text">{sig_sub}</div>
        </div>
    """, unsafe_allow_html=True)

with col_kpi:
    k1, k2, k3, k4 = st.columns(4)
    if is_calibrated:
        k1.metric("Spread", f"{curr_spread:.5f}")
        k2.metric("Beta (β)", f"{curr_beta:.3f}")
        k3.metric("Z-Score", f"{curr_z:.2f}", delta=f"{z_delta:.2f}", delta_color="inverse")
        k4.metric("Corr (ρ)", f"{curr_corr:.2f}")
    else:
        k1.metric("Spread", "---")
        k2.metric("Beta (β)", "---")
        k3.metric("Z-Score", "---")
        k4.metric("Corr (ρ)", "---")

# --- 7. PROFESSIONAL CHARTING (Plotly) ---
# Create 4-pane chart (Price, Spread, Z-Score, Volume)
fig = make_subplots(
    rows=4, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.10, 
    row_heights=[0.35, 0.2, 0.2, 0.15], 
    subplot_titles=(
        f"Price Action ({sym_y} vs {sym_x})", 
        "Spread Analysis", 
        "Z-Score Signal",
        "Liquidity Profile"
    )
)

# Pane 1: Prices (Dual Axis)
fig.add_trace(go.Scatter(x=analytics_df.index, y=analytics_df['y'], name=sym_y, line=dict(color='#00F0FF', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=analytics_df.index, y=analytics_df['x'], name=sym_x, line=dict(color='#FFA500', width=2), yaxis='y2'), row=1, col=1)

if is_calibrated:
    # Pane 2: Spread
    fig.add_trace(go.Scatter(x=analytics_df.index, y=analytics_df['spread'], name="Spread", line=dict(color='#E0E0E0', width=1.5), fill='tozeroy', fillcolor='rgba(224, 224, 224, 0.05)'), row=2, col=1)
    roll_mean = analytics_df['spread'].rolling(window=window).mean()
    fig.add_trace(go.Scatter(x=analytics_df.index, y=roll_mean, name=f"MA({window})", line=dict(color='#888', width=1, dash='dot')), row=2, col=1)

    # Pane 3: Z-Score
    z_vals = analytics_df['z_score']
    colors = ['#FF4B4B' if z > z_thresh else '#00FF7F' if z < -z_thresh else '#555' for z in z_vals]
    fig.add_trace(go.Bar(x=analytics_df.index, y=z_vals, name="Z-Score", marker_color=colors), row=3, col=1)
    fig.add_hline(y=z_thresh, line_dash="dash", line_color="rgba(255, 75, 75, 0.5)", row=3, col=1)
    fig.add_hline(y=-z_thresh, line_dash="dash", line_color="rgba(0, 255, 127, 0.5)", row=3, col=1)

# Pane 4: Volume (New)
if 'vol_x' in analytics_df.columns:
    fig.add_trace(go.Bar(x=analytics_df.index, y=analytics_df['vol_x'], name="Vol X", marker_color='#FFA500', opacity=0.5), row=4, col=1)
    fig.add_trace(go.Bar(x=analytics_df.index, y=analytics_df['vol_y'], name="Vol Y", marker_color='#00F0FF', opacity=0.5), row=4, col=1)

# Global Chart Layout Updates
fig.update_layout(
    height=900, 
    template="plotly_dark",
    paper_bgcolor='rgba(0,0,0,0)', 
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=20, r=20, t=100, b=20), 
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="right", x=1, bgcolor='rgba(0,0,0,0)'),
    yaxis2=dict(overlaying='y', side='right', showgrid=False, title=sym_x),
    yaxis=dict(title=sym_y),
    font=dict(family="Inter, sans-serif")
)

# Remove gridlines for cleaner look on lower subplots
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#333', row=1, col=1)
fig.update_yaxes(showgrid=False, row=2, col=1)
fig.update_yaxes(showgrid=False, row=3, col=1)
fig.update_yaxes(showgrid=False, row=4, col=1)

st.plotly_chart(fig, use_container_width=True)

# --- 8. DETAILED ANALYSIS TABS ---
t1, t2, t3 = st.tabs(["📊 Performance Backtest", "📋 Resampled Stats (1m)", "🔍 Market Data Inspection"])

with t1:
    if is_calibrated:
        st.markdown("##### In-Sample Session Backtest")
        bt_df = QuantEngine.run_backtest(analytics_df, z_thresh, exit_thresh)
        
        if bt_df is not None:
            bc1, bc2 = st.columns([3, 1])
            with bc1:
                fig_bt = go.Figure(go.Scatter(x=bt_df.index, y=bt_df['cum_pnl'], fill='tozeroy', line=dict(color='#00FF7F', width=2), name="Cumulative PnL"))
                fig_bt.update_layout(height=250, template="plotly_dark", margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bt, use_container_width=True)
            with bc2:
                st.markdown("<br>", unsafe_allow_html=True) 
                total_pnl = bt_df['cum_pnl'].iloc[-1]
                trade_count = len(bt_df[bt_df['position'].diff() != 0])
                st.metric("Session PnL", f"{total_pnl:.4f}")
                st.metric("Signal Flips", f"{trade_count}")
    else:
        st.info("Waiting for calibration for backtest...")

with t2:
    st.markdown("##### 1-Minute Aggregated Statistics")
    if not analytics_df.empty:
        resampled_df = QuantEngine.resample_data(analytics_df, '1min')
        st.dataframe(resampled_df.style.format("{:.4f}"), use_container_width=True)
        st.download_button("Download 1-Min Data (CSV)", resampled_df.to_csv().encode('utf-8'), "statarb_1min.csv", "text/csv")

with t3:
    col_insp_1, col_insp_2 = st.columns([1, 2])
    
    with col_insp_1:
        st.markdown("##### Stationarity (ADF Test)")
        if is_calibrated:
            adf_res = QuantEngine.run_stationarity_test(analytics_df['spread'])
            if adf_res:
                is_stat = adf_res['is_stationary']
                stat_color = "green" if is_stat else "red"
                stat_msg = "STATIONARY (Mean Reverting)" if is_stat else "NON-STATIONARY (Trending)"
                st.markdown(f"""
                <div style="background-color: #1a1c24; padding: 10px; border-radius: 5px; border-left: 4px solid {stat_color};">
                    <strong style="color: {stat_color}">{stat_msg}</strong>
                    <br><span style="font-size: 0.9em; color: #888">p-value: {adf_res['p_value']:.4f}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Insufficient data for ADF test.")
    
    with col_insp_2:
        st.markdown("##### Latest Tick Data")
        cols_to_show = ['x', 'y', 'spread', 'z_score']
        if set(cols_to_show).issubset(analytics_df.columns):
            st.dataframe(analytics_df.tail(10)[cols_to_show].style.format("{:.4f}"), use_container_width=True)
        else:
            st.dataframe(analytics_df.tail(5), use_container_width=True)
        
        st.download_button("Download Tick Data (CSV)", analytics_df.to_csv().encode('utf-8'), "statarb_ticks.csv", "text/csv")

# --- 9. AUTO REFRESH LOOP ---
if auto_refresh and data_source == "Live Stream":
    time.sleep(config.REFRESH_RATE_MS / 1000.0)
    st.rerun()