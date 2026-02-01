import pandas as pd
from engine.order import Trade

class Tape:
    def __init__(self):
        self.trades = []

    def log_trade(self,timestamp, price, qty, buyer, seller, aggressor):
        self.trades.append({
            'timestamp': timestamp,
            'price': price,
            'qty': qty,
            'buyer': buyer,
            'seller': seller,
            'aggressor': aggressor
        })
    def to_dataframe(self):
        df=pd.DataFrame(self.trades)
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
    def record_trade(self, trade: Trade):
        self.trades.append(trade.to_dict())