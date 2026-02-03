import pandas as pd
import heapq
from engine.matching_engine import MatchingEngine

class SnapshotRecorder:
    def __init__(self):
        self.l1_snapshots = []
        self.l2_snapshots = []

    def record_snapshot(self, engine: MatchingEngine, timestamp):
        l1_data = engine.get_snapshot()
        l1_data['timestamp'] = timestamp
        self.l1_snapshots.append(l1_data)

        depth = 5
        
        best_bids = heapq.nsmallest(depth, engine.bids)
        best_asks = heapq.nsmallest(depth, engine.asks)
        
        bids_l2 = [(-p, o.qty) for p, t, o in best_bids]
        asks_l2 = [(p, o.qty) for p, t, o in best_asks]

        self.l2_snapshots.append({
            'timestamp': timestamp,
            'bids': bids_l2,
            'asks': asks_l2
        })

        return l1_data['mid_price'], l1_data['spread'], self.l1_snapshots[-1], self.l2_snapshots[-1]

    def get_l1_dataframe(self):
        df = pd.DataFrame(self.l1_snapshots)
        if not df.empty and 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('datetime', inplace=True)
        return df
    
    def get_l2_dataframe(self):
        df = pd.DataFrame(self.l2_snapshots)
        if not df.empty and 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
