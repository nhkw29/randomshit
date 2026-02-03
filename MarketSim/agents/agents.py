import numpy as np
from engine.order import Order
import random
from abc import ABC, abstractmethod
from collections import deque

class BaseAgent(ABC):
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.inventory = 0
        self.balance = 0

    @abstractmethod
    def act(self, snapshot):
        pass
    
class MarketMaker(BaseAgent):
    def __init__(self, agent_id, inventory_limit=1000, skew_factor=0.01):
        super().__init__(agent_id)
        self.inventory_limit = inventory_limit
        self.skew_factor = skew_factor

    def act(self, snapshot):
        mid_price = snapshot.get('mid_price', 100.0)
        # Fallback to 0.10 spread instead of 1.0 to encourage tightness
        last_spread = snapshot.get('spread', 0.10)
        
        q = self.inventory
        if abs(q) >= self.inventory_limit:
            return None

        reservation_price = mid_price - (q * self.skew_factor)
        
        # --- FIX: DYNAMIC SPREAD ---
        # Add slight randomness to spread to prevent "flatline" charts
        # Varies between 90% and 110% of the last known spread
        target_spread = max(0.02, last_spread * random.uniform(0.9, 1.1))
        
        half_spread = target_spread / 2
        
        bid_price = max(0.01, round(reservation_price - half_spread, 2))
        ask_price = max(0.01, round(reservation_price + half_spread, 2))
        
        # Ensure minimal viable spread
        if ask_price <= bid_price:
            ask_price = bid_price + 0.05
        
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
    def __init__(self, agent_id, sigma=0.5):
        super().__init__(agent_id)
        self.sigma = sigma
        
    def act(self, snapshot):
        fair_value = snapshot.get('fair_value', snapshot.get('mid_price', 100.0))
        
        side = random.choice(['buy', 'sell'])
        trade_size = random.randint(1, 20)
        
        # Noise traders create volatility
        price_variation = np.random.normal(0, self.sigma)
        price = fair_value + price_variation if side == 'buy' else fair_value - price_variation
        
        price = max(0.01, round(price, 2))
        
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
        current_mid = snapshot.get('mid_price', 100.0)
        self.price_history.append(current_mid)
        
        if len(self.price_history) < self.window_size:
            return None
        
        sma = np.mean(self.price_history)
        
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
