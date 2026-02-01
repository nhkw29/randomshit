import pandas as pd
import mplfinance as mpf
from .metrics import MarketMetrics
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

class MarketPlots:
    def __init__(self, recorder, tape):
        self.recorder = recorder
        self.tape = tape
        self.metrics = MarketMetrics(tape)

    def generate_scenario_report(self, pdf, scenario_name):
        df_l1 = self.recorder.get_l1_dataframe()
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 11), gridspec_kw={'height_ratios': [2, 1]})
        fig.suptitle(f"Market Report: {scenario_name}", fontsize=16)

        ohlc = df_l1['mid_price'].resample('1min').ohlc()
        mpf.plot(ohlc, type='candle', ax=ax1, style='charles', show_nontrading=False)
        ax1.set_title("Mid-Price OHLC (1-min)")

        ax2.plot(df_l1.index, df_l1['spread'], color='orange', label='Bid-Ask Spread')
        ax2.set_title("Spread Dynamics")
        ax2.set_ylabel("Spread Value")
        ax2.legend()

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        pdf.savefig(fig)
        plt.close(fig)
