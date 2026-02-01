import pandas as pd
import mplfinance as mpf
from .metrics import MarketMetrics
import matplotlib.pyplot as plt

class MarketPlots:
    def __init__(self, tape: pd.DataFrame):
        self.metrics = MarketMetrics(tape)

    def plot_vwap(self):
        vwap = self.metrics.compute_vwap()
        print(f"VWAP: {vwap}")
        return vwap

    def plot_ohlc(self, freq='1Min'):
        ohlc = self.metrics.get_ohlc_data(freq)
        if ohlc is None:
            print("No data to plot OHLC.")
            return
        
        mpf.plot(ohlc, type='candle', style='charles', title='OHLC Chart', ylabel='Price')
        plt.show()