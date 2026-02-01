import pandas as pd
import numpy as np
from .tape import Tape
from .snapshots import SnapshotRecorder

class MarketMetrics:
    def __init__(self, tape: Tape):
        self.tape = tape

    def compute_vwap(self):
        df = self.tape.to_dataframe()
        if df.empty:
            return None
        total_dollar_volume=(df['price']*df['qty']).sum()
        total_volume = df['qty'].sum()
        vwap = total_dollar_volume / total_volume
        return vwap

    def get_session_volatility(self):
        df = self.l1_dataframe()
        if df.empty:
            return None
        
        resampled_mid = df['mid_price'].resample('1S').last().dropna()
        log_returns = np.log(resampled_mid / resampled_mid.shift(1)).dropna()
        volatility = log_returns.std()
        return volatility
    
    def get_rolling_volatility(self, window_size=60):
        df = self.l1_dataframe()
        if df.empty:
            return None
        
        resampled_mid = df['mid_price'].resample('1S').last().dropna()
        log_returns = np.log(resampled_mid / resampled_mid.shift(1)).dropna()
        rolling_volatility = log_returns.rolling(window=window_size).std()
        return rolling_volatility
    def get_ohlc_data(self, freq='1Min'):
        df = self.l1_dataframe()
        if df.empty:
            return None
        
        ohlc = df['mid_price'].resample(freq).ohlc()
        return ohlc
    