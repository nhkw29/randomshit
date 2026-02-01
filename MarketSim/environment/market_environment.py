import gymnasium as gym
from gymnasium import spaces
import numpy as np 
import random

from engine.matching_engine import MatchingEngine
from engine.order import Order
from agents.agents import KyleNoiseTrader, InventoryMarketMaker
from engine.event_loop import EventLoop

class GymTradingEnvironment(gym.Env):
    def __init__(self):
        super(GymTradingEnvironment, self).__init__()

        self.loop = EventLoop()
        
        self.action_space = spaces.Box(low=-1, high=1, shape=(3,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32)

        self.order_book = None
        self.agents = []
        self.max_steps = 1000
        
        self.insider_inventory = 0
        self.cash_balance = 100000
        self.tape_reader_index=0
        self.latency_mu=0.005
        self.latency_sigma=0.001

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.loop = EventLoop()
        self.order_book = MatchingEngine()
        self.insider_inventory = 0
        self.cash_balance = 100000
        self.agents = []

        for i in range(5): 
            self.agents.append(InventoryMarketMaker(f"MM_{i}"))
        for i in range(10): 
            self.agents.append(KyleNoiseTrader(f"NT_{i}", sigma_n=3.0))

        random.shuffle(self.agents)

        self.loop.schedule(0.1,self._background_agent_step)
        self.loop.run_until(20.0)

        self.tape_reader_index=len(self.order_book.tape)
        return self._get_obs(), {}

    def step(self, action):
        current_time = self.loop.current_time
        
        side_val, agg_val, qty_val = action
        
        side = 'buy' if side_val > 0 else 'sell'
        qty = int((qty_val + 1) / 2 * 100)
        
        if qty > 0:

            def place_insider_order():
                
                snap = self.order_book.get_snapshot()
                mid = snap['mid_price']
            
                offset = agg_val * 2.0
                if side == 'buy': price = mid + offset
                else: price = mid - offset
            
                insider_order = Order(
                    agent_id="Insider",
                    side=side,
                    price=round(price, 2),
                    qty=qty,
                    order_type='limit',
                    timestamp=self.loop.current_time
                )
                self.order_book.add_order(insider_order)
            
            self.loop.schedule(0.05, place_insider_order)
        
        target_time = current_time + 1.0
        self.loop.run_until(target_time)

        current_tape=self.order_book.tape
        current_tape_length=len(current_tape)

        for i in range(self.tape_reader_index,current_tape_length):
            trade=current_tape[i]
            if trade.buyer_id == "Insider":
                self.insider_inventory += trade.qty
                self.cash_balance -= trade.qty * trade.price
            elif trade.seller_id == "Insider":
                self.insider_inventory -= trade.qty
                self.cash_balance += trade.qty * trade.price
        
        self.tape_reader_index=current_tape_length
        
        current_mid = self.order_book.get_snapshot()['mid_price']
        portfolio_value = self.cash_balance + (self.insider_inventory * current_mid)

        reward = (portfolio_value - 100000) / 100

        terminated = self.cash_balance<=0
        truncated = self.loop.current_time >= (self.max_steps+20.0)

        try:
            self.order_book.run_sanity_check()
        except AssertionError as e:
            print(f"SIMULATION CRASHED: {e}")
            return self._get_obs(), -1000.0, True, False, {"error": str(e)}
        
        return self._get_obs(), reward, terminated, truncated, {}

    def _get_obs(self):
        snap = self.order_book.get_snapshot()
        return np.array([
            snap['best_bid'],
            snap['best_ask'],
            snap['mid_price'],
            snap['spread'],
            self.insider_inventory,
            self.cash_balance
        ], dtype=np.float32)

    def _background_agent_step(self):
        agent= random.choice(self.agents)
        snap = self.order_book.get_snapshot()
        orders = agent.act(snap)
        if not isinstance(orders, list):
            orders = [orders]
        for order in orders:
            order.timestamp = self.loop.current_time
            self.order_book.add_order(order)
        next_delay = random.uniform(0.1, 0.5)
        self.loop.schedule(next_delay, self._background_agent_step)
