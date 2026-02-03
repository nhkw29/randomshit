import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from .metrics import MarketMetrics

class MarketPlots:
    def __init__(self, recorder, tape):
        self.recorder = recorder
        self.tape = tape

    def generate_scenario_report(self, pdf, scenario_name):
        print(f"Generating report for: {scenario_name}...")
        
        df_l1 = self.recorder.get_l1_dataframe()
        
        if df_l1.empty:
            print(f"Warning: No data found for {scenario_name}.")
            return

        # --- FIX 1: AGGRESSIVE TRIM ---
        # Removes the first 60 seconds of data
        if len(df_l1) > 60:
            df_l1 = df_l1.iloc[60:]
        
        try:
            # --- FIX 2: 30s Resampling ---
            ohlc = df_l1['mid_price'].resample('30s').ohlc().dropna()
        except Exception as e:
            print(f"Resampling error: {e}")
            return

        if ohlc.empty:
            print(f"Warning: Not enough data for {scenario_name}.")
            return

        # Calculate Stats
        avg_spread = df_l1['spread'].mean()
        returns = df_l1['mid_price'].pct_change().dropna()
        volatility = returns.std() * (len(df_l1)**0.5) if not returns.empty else 0.0

        # --- FIX 3: Layout Spacing ---
        fig = plt.figure(figsize=(11, 8.5))
        gs = fig.add_gridspec(3, 1, height_ratios=[0.15, 2, 1], hspace=0.35)
        
        # Header
        ax_header = fig.add_subplot(gs[0])
        ax_header.axis('off')
        
        ax_header.text(0.5, 0.75, f"{scenario_name}", ha='center', va='center', fontsize=16, fontweight='bold', color='#333')
        ax_header.text(0.5, 0.25, f"Avg Spread: ${avg_spread:.2f}  |  Realized Vol: {volatility:.4f}  |  Duration: {len(df_l1)} ticks", 
                       ha='center', va='center', fontsize=12, color='#555')

        # Candle Chart
        ax1 = fig.add_subplot(gs[1])
        mc = mpf.make_marketcolors(up='#00b060', down='#fe3032', edge='inherit', wick='inherit', volume='in')
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', gridcolor='#d9d9d9', y_on_right=True)
        
        mpf.plot(ohlc, type='candle', ax=ax1, style=s, 
                 warn_too_much_data=10000,
                 ylabel='Price ($)',
                 axtitle='Mid-Price Dynamics (30s Candles)')

        # Spread Chart
        ax2 = fig.add_subplot(gs[2], sharex=ax1)
        ax2.plot(df_l1.index, df_l1['spread'], color='#ff7f0e', linewidth=1.2, label='Spread')
        ax2.fill_between(df_l1.index, df_l1['spread'], color='#ff7f0e', alpha=0.2)
        
        # --- FIX 4: Y-Axis Clamping ---
        high_limit = df_l1['spread'].quantile(0.95)
        if high_limit > 0:
            ax2.set_ylim(0, max(2.0, high_limit * 1.5))
        
        ax2.set_title("Bid-Ask Spread Stress", fontsize=10, fontweight='bold', loc='left')
        ax2.set_ylabel("Spread ($)")
        ax2.grid(True, linestyle=':', alpha=0.6)
        
        fig.autofmt_xdate()

        pdf.savefig(fig)
        plt.close(fig)
        print(f"Successfully saved page for {scenario_name}")
