import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

class KalmanFilterReg:
    """
    Bonus: Online Kalman Filter for Dynamic Hedge Ratio estimation.
    This adapts to changing beta faster than OLS rolling windows.
    State Space Model:
    y_t = beta_t * x_t + epsilon_t
    beta_t = beta_{t-1} + nu_t
    """
    def __init__(self, delta=1e-4, R=1e-3):
        # delta: Process noise variance (flexibility of beta)
        # R: Measurement noise variance
        self.delta = delta 
        self.R = R
        self.beta = np.zeros(2) # [intercept, slope]
        self.P = np.eye(2)      # Covariance matrix
        
    def update(self, x, y):
        # x: Independent variable (e.g., BTC returns)
        # y: Dependent variable (e.g., ETH returns)
        
        # Observation matrix H = [1, x]
        H = np.array([1.0, x])
        
        # Prediction (Random Walk Prior)
        # beta_pred = beta_prev
        # P_pred = P_prev + Q
        Q = self.delta * np.eye(2)
        P_pred = self.P + Q
        
        # Measurement update
        y_pred = H @ self.beta
        error = y - y_pred
        
        # Kalman Gain
        S = H @ P_pred @ H.T + self.R
        K = P_pred @ H.T / S
        
        # Update State
        self.beta = self.beta + K * error
        self.P = (np.eye(2) - np.outer(K, H)) @ P_pred
        
        return self.beta[1], self.beta[0] # slope, intercept

class QuantEngine:
    @staticmethod
    def prepare_aligned_data(df: pd.DataFrame, sym_x: str, sym_y: str):
        """
        Aligns prices by timestamp using pivot and ffill.
        Returns clean dataframe with 'x' and 'y' columns.
        """
        if df.empty: return pd.DataFrame()

        # Work on a copy to avoid side effects and allow column normalization
        df = df.copy()
        
        # Normalize columns: Strip whitespace and convert to lowercase
        # This fixes issues where CSV headers have spaces like " price"
        df.columns = df.columns.str.strip().str.lower()
        
        # --- NEW: Handle Pre-Aligned / Analytics Export Data (Wide Format) ---
        # If the file already contains 'x' and 'y' columns (like the statarb_analytics.csv)
        if {'x', 'y'}.issubset(df.columns):
            # Ensure timestamp is available as index
            if 'timestamp' in df.columns:
                if not np.issubdtype(df['timestamp'].dtype, np.datetime64) and not np.issubdtype(df['timestamp'].dtype, np.number):
                     df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
            
            # Construct data frame with expected columns
            data = pd.DataFrame({
                'x': df['x'],
                'y': df['y'],
                'vol_x': df['vol_x'] if 'vol_x' in df.columns else 0,
                'vol_y': df['vol_y'] if 'vol_y' in df.columns else 0
            })
            return data.sort_index()
        # ---------------------------------------------------------------------
        
        # Map common aliases to standard names
        # Price Aliases
        if 'close' in df.columns and 'price' not in df.columns:
            df = df.rename(columns={'close': 'price'})
        if 'last' in df.columns and 'price' not in df.columns:
            df = df.rename(columns={'last': 'price'})
            
        # Symbol Aliases
        if 'ticker' in df.columns and 'symbol' not in df.columns:
            df = df.rename(columns={'ticker': 'symbol'})
        if 'pair' in df.columns and 'symbol' not in df.columns:
            df = df.rename(columns={'pair': 'symbol'})
        if 'instrument' in df.columns and 'symbol' not in df.columns:
            df = df.rename(columns={'instrument': 'symbol'})
            
        # Timestamp Aliases
        if 'date' in df.columns and 'timestamp' not in df.columns:
            df = df.rename(columns={'date': 'timestamp'})
        if 'time' in df.columns and 'timestamp' not in df.columns:
            df = df.rename(columns={'time': 'timestamp'})
        if 'datetime' in df.columns and 'timestamp' not in df.columns:
            df = df.rename(columns={'datetime': 'timestamp'})
            
        # Validate required columns
        required_cols = {'timestamp', 'symbol', 'price'}
        if not required_cols.issubset(df.columns):
            # Debugging hint: user might need to know which cols are missing
            # print(f"Missing columns: {required_cols - set(df.columns)}")
            return pd.DataFrame()
        
        # Ensure timestamp is datetime
        if not np.issubdtype(df['timestamp'].dtype, np.datetime64) and not np.issubdtype(df['timestamp'].dtype, np.number):
             df['timestamp'] = pd.to_datetime(df['timestamp'])

        pivot = df.pivot_table(index='timestamp', columns='symbol', values='price')
        
        # --- NEW: Capture Volume for Liquidity Profile ---
        # Check for 'size' or 'volume' column
        vol_col = None
        if 'size' in df.columns: vol_col = 'size'
        elif 'volume' in df.columns: vol_col = 'volume'
        elif 'qty' in df.columns: vol_col = 'qty'
        
        if vol_col:
            vol_pivot = df.pivot_table(index='timestamp', columns='symbol', values=vol_col, aggfunc='sum')
            vol_pivot = vol_pivot.fillna(0)
        else:
            vol_pivot = pd.DataFrame()
        # -------------------------------------------------

        pivot = pivot.ffill().dropna()
        
        # Critical Check: Ensure selected symbols exist in the data
        if sym_x not in pivot.columns or sym_y not in pivot.columns:
            # This is a common failure point if the CSV symbols don't match the Sidebar selection
            return pd.DataFrame()
            
        data = pd.DataFrame({
            'x': pivot[sym_x],
            'y': pivot[sym_y],
            'vol_x': vol_pivot[sym_x] if not vol_pivot.empty and sym_x in vol_pivot.columns else 0,
            'vol_y': vol_pivot[sym_y] if not vol_pivot.empty and sym_y in vol_pivot.columns else 0
        })
        return data

    @staticmethod
    def calculate_metrics(df: pd.DataFrame, window=20, method='OLS'):
        """
        Core analytics pipeline.
        Calculates Spread, Z-Score, and Rolling Beta.
        """
        # MODIFIED: Allow returning partial dataframe for progressive loading
        if len(df) < window:
            # Return df with NaNs for metrics so we can still plot prices
            return df
        
        df = df.copy()
        
        # 1. Beta Calculation
        if method == 'OLS':
            # Rolling OLS
            rolling_cov = df['x'].rolling(window=window).cov(df['y'])
            rolling_var = df['x'].rolling(window=window).var()
            df['beta'] = rolling_cov / rolling_var
            
            rolling_mean_y = df['y'].rolling(window=window).mean()
            rolling_mean_x = df['x'].rolling(window=window).mean()
            df['alpha'] = rolling_mean_y - df['beta'] * rolling_mean_x
            
            df['spread'] = df['y'] - (df['beta'] * df['x'] + df['alpha'])
            
        elif method == 'Kalman':
            # Apply Kalman Filter Iteratively
            kf = KalmanFilterReg()
            betas = []
            alphas = []
            
            for i in range(len(df)):
                slope, intercept = kf.update(df['x'].iloc[i], df['y'].iloc[i])
                betas.append(slope)
                alphas.append(intercept)
                
            df['beta'] = betas
            df['alpha'] = alphas
            df['spread'] = df['y'] - (df['beta'] * df['x'] + df['alpha'])

        elif method == 'Robust (Huber)':
            # --- NEW: Robust Regression (Rolling Median/Theil-Sen Proxy) ---
            df['beta'] = (df['y'] / df['x']).rolling(window=window).median()
            
            rolling_median_y = df['y'].rolling(window=window).median()
            rolling_median_x = df['x'].rolling(window=window).median()
            df['alpha'] = rolling_median_y - df['beta'] * rolling_median_x
            df['spread'] = df['y'] - (df['beta'] * df['x'] + df['alpha'])

        # 2. Z-Score Calculation
        roll_mean = df['spread'].rolling(window=window).mean()
        roll_std = df['spread'].rolling(window=window).std()
        
        # Handle division by zero (rare but possible in flat markets)
        df['z_score'] = (df['spread'] - roll_mean) / (roll_std + 1e-8)
        
        return df # Do not dropna here to allow viewing prices while Z-score calibrates

    @staticmethod
    def resample_data(df: pd.DataFrame, rule='1min'):
        """
        NEW: Resamples tick data into OHLCV + Mean Stats
        """
        if df.empty: return pd.DataFrame()
        
        # Only aggregate columns that exist
        agg_dict = {'x': 'last', 'y': 'last'}
        if 'vol_x' in df.columns: agg_dict['vol_x'] = 'sum'
        if 'vol_y' in df.columns: agg_dict['vol_y'] = 'sum'
        if 'spread' in df.columns: agg_dict['spread'] = 'mean'
        if 'z_score' in df.columns: agg_dict['z_score'] = 'last'
        if 'beta' in df.columns: agg_dict['beta'] = 'last'

        return df.resample(rule).agg(agg_dict).dropna()

    @staticmethod
    def run_stationarity_test(spread_series):
        """Performs Augmented Dickey-Fuller Test."""
        clean_series = spread_series.dropna()
        if len(clean_series) < 30:
            return None
        
        try:
            result = adfuller(clean_series)
            return {
                'adf_stat': result[0],
                'p_value': result[1],
                'is_stationary': result[1] < 0.05
            }
        except:
            return None

    @staticmethod
    def run_backtest(df: pd.DataFrame, entry_z=2.0, exit_z=0.0):
        """
        Vectorized Mini-Backtest.
        Logic: Short Spread when Z > 2, Long Spread when Z < -2. Exit at 0.
        """
        if 'z_score' not in df.columns: return None
        
        df = df.copy().dropna(subset=['z_score'])
        if df.empty: return None

        df['position'] = 0
        
        # Vectorized Signal Logic (Simplified)
        # 1 = Long Spread (Long Y, Short X)
        # -1 = Short Spread (Short Y, Long X)
        
        # Entry
        df.loc[df['z_score'] < -entry_z, 'position'] = 1
        df.loc[df['z_score'] > entry_z, 'position'] = -1
        
        # Fill forward positions until exit condition is met (Stateful, harder to pure vectorize)
        # We do a simple approach: Carry forward position if abs(z) > exit_z
        # This is an approximation for visualization
        
        positions = np.zeros(len(df))
        current_pos = 0
        
        z = df['z_score'].values
        
        for i in range(1, len(df)):
            if z[i] > entry_z:
                current_pos = -1 # Short spread
            elif z[i] < -entry_z:
                current_pos = 1 # Long spread
            elif (current_pos == 1 and z[i] >= exit_z) or (current_pos == -1 and z[i] <= -exit_z):
                current_pos = 0 # Exit
            
            positions[i] = current_pos
            
        df['position'] = positions
        
        # Calculate PnL: Position * Change in Spread
        df['spread_ret'] = df['spread'].diff()
        df['pnl'] = df['position'].shift(1) * df['spread_ret']
        df['cum_pnl'] = df['pnl'].cumsum()
        
        return df