import pandas as pd
import heapq
from engine.matching_engine import MatchingEngine

class SnapshotRecorder:
    def __init__(self):
        self.l1_snapshots = []
        self.l2_snapshots = []

    def record_snapshot(self,engine, timestamp):
        l1_data = engine.get_snapshot()
        l1_data['timestamp'] = timestamp
        self.l1_snapshots.append(l1_data)

        depth=5

        best_bids=heapq.nsmallest(depth, engine.bids)
        best_asks=heapq.nsmallest(depth, engine.asks)
        bid_levels=[(-price, order.qty) for price, _, order in best_bids]
        ask_levels=[(price, order.qty) for price, _, order in best_asks]

        mid_price = (bid_levels[0][0] + ask_levels[0][0]) / 2 if bid_levels and ask_levels else None

        self.l2_snapshots.append({
            'timestamp': timestamp,
            'bids': bid_levels,
            'asks': ask_levels
        })

    def get_l1_dataframe(self):
        df=pd.DataFrame(self.l1_snapshots)
        if not df.empty and 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
    def get_l2_dataframe(self):
        df=pd.DataFrame(self.l2_snapshots)
        if not df.empty and 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df