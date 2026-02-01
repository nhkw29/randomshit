import numpy as np
from engine.order import Order
import random

class BaseAgent:
    def act(self, snapshot, book): pass
class KyleNoiseTrader(BaseAgent):
    def __init__(self, id, mu=0, sigma=1, qty_mean=10, qty_std=5):
        self.id = id
        self.mu = mu
        self.sigma = sigma
        self.qty_mean = qty_mean
        self.qty_std = qty_std

    def act(self, snapshot, book):
        side = random.choice(['buy', 'sell'])
        price = max(1, np.random.normal(self.mu, self.sigma))
        qty = max(1, int(np.random.normal(self.qty_mean, self.qty_std)))
        order = Order(self.id, side, price, qty)
        return order
class InventoryMarketMaker(BaseAgent):
    def __init__(self, id, spread=1.0, inventory_limit=100):
        self.id = id
        self.spread = spread
        self.inventory = 0
        self.inventory_limit = inventory_limit

    def act(self, snapshot, book):
        mid_price = (snapshot['best_bid'] + snapshot['best_ask']) / 2
        orders = []

        if self.inventory < self.inventory_limit:
            bid_price = mid_price - self.spread / 2
            bid_order = Order(self.id, 'buy', bid_price, qty=10)
            orders.append(bid_order)

        if self.inventory > -self.inventory_limit:
            ask_price = mid_price + self.spread / 2
            ask_order = Order(self.id, 'sell', ask_price, qty=10)
            orders.append(ask_order)

        return orders