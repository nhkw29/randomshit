import pandas as pd
import heapq
from engine.matching_engine import MatchingEngine

class SnapshotRecorder:
    def __init__(self):
        self.l1_snapshots = []
        self.l2_snapshots = []

    def record_snapshot(self,engine:MatchingEngine, timestamp):
        l1_data = engine.get_snapshot()
        l1_data['timestamp'] = timestamp
        self.l1_snapshots.append(l1_data)

        depth=5

        best_bids=heapq.nsmallest(depth, engine.bids)
        best_asks=heapq.nsmallest(depth, engine.asks)
        bid_levels=[(-price, order.qty) for price, _, order in best_bids]
        ask_levels=[(price, order.qty) for price, _, order in best_asks]

        mid_price = (bid_levels[0][0] + ask_levels[0][0]) / 2 if bid_levels and ask_levels else None
        spread = ask_levels[0][0] - bid_levels[0][0] if bid_levels and ask_levels else None

        bid_ladder = {}
        for price_val, ts, order in engine.bids:
            p = -price_val
            bid_ladder[p] = bid_ladder.get(p, 0) + order.qty
        
        ask_ladder = {}
        for price_val, ts, order in engine.asks:
            ask_ladder[price_val] = ask_ladder.get(price_val, 0) + order.qty

        self.l2_snapshots.append({
            'timestamp': timestamp,
            'bids': sorted(bid_ladder.items(), reverse=True)[:5],
            'asks': sorted(ask_ladder.items())[:5]
        })
        return mid_price, spread, self.l1_snapshots[-1], self.l2_snapshots[-1]

    def get_l1_dataframe(self):
        df=pd.DataFrame(self.l1_snapshots)
        if not df.empty and 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('datetime', inplace=True)
        return df
    def get_l2_dataframe(self):
        df=pd.DataFrame(self.l2_snapshots)
        if not df.empty and 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
