import numpy as np
from engine.order import Order
import random
from abc import ABC, abstractmethod
from analytics.snapshots import SnapshotRecorder
from collections import deque

class BaseAgent(ABC):
    def __init__(self,agent_id):
        self.agent_id=agent_id
        self.inventory=0
        self.balance=0
    @abstractmethod
    def act(self,snapshot:SnapshotRecorder.record_snapshot):
        pass
    
class MarketMaker(BaseAgent):
    def __init__ (self, agent_id, inventory_limit=100, skew_factor=0.01):
        super().__init__(agent_id)
        self.inventory_limit = inventory_limit
        self.skew_factor = skew_factor

    def act(self, snapshot):
        mid_price = snapshot.l1_snapshots[-1]['mid_price'] if snapshot.l1_snapshots else 100.0
        spread=snapshot.l1_snapshots[-1]['spread'] if snapshot.l1_snapshots else 1.0
        q=self.inventory
        if q <= -self.inventory_limit or q >= self.inventory_limit:
            return None
        reservation_price=mid_price-self.inventory*self.skew_factor
        bid_price=round(reservation_price-spread/2,2)
        ask_price=round(reservation_price+spread/2,2)
        qty = random.randint(1, 10)
        return [
            {
                'type': 'PLACE_LIMIT',
                'side': 'buy',
                'price': bid_price,
                'qty': qty,
                'agent_id': self.agent_id
            },
            {
                'type': 'PLACE_LIMIT',
                'side': 'sell',
                'price': ask_price,
                'qty': qty,
                'agent_id': self.agent_id
            }
        ]

class NoiseTrader(BaseAgent):
    def __init__(self, agent_id,sigma=2.0):
        super().__init__(agent_id)
        self.sigma=sigma
        
    def act(self, snapshot):
        side = random.choice(['buy', 'sell'])
        trade_size = random.randint(1, 20)
        fair_value = snapshot.l1_snapshots[-1]['fair_value'] if snapshot.l1_snapshots else 100.0
        price_variation = np.random.normal(0, self.sigma)
        price = fair_value + price_variation if side == 'buy' else fair_value - price_variation
        price = max(1.0, round(price, 2))
        return {
            'type': 'PLACE_LIMIT',
            'side': side,
            'price': price,
            'qty': trade_size,
            'agent_id': self.agent_id
        }

class MomentumTrader(BaseAgent):
    def __init__(self, agent_id, window_size=50):
        super().__init__(agent_id)
        self.window_size = window_size
        self.price_history = deque(maxlen=window_size)
    
    def act(self, snapshot):
        fair_value = snapshot.l1_snapshots[-1]['fair_value'] if snapshot.l1_snapshots else 100.0
        current_mid = snapshot.l1_snapshots[-1]['mid_price'] if snapshot.l1_snapshots else fair_value
        self.price_history.append(current_mid)
        
        if len(self.price_history) < self.window_size:
            return None
        
        sma=np.mean(self.price_history)
        
        if current_mid > sma:
            side = 'buy'
        elif current_mid < sma:
            side = 'sell'
        else:
            return None
        
        trade_size = random.randint(5, 15)
        
        return {
            'type': 'PLACE_MARKET',
            'side': side,
            'qty': trade_size,
            'agent_id': self.agent_id
        }
        
