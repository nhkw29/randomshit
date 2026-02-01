from dataclasses import dataclass, field
from typing import Optional

@dataclass(slots=True)
class Order:
    agent_id: str
    side: str
    qty: int
    price: Optional[float] = None
    order_type: str = 'limit'
    timestamp: float = 0.0
    order_id: int = 0
    status: str='open'

    def __post_init__(self):
        self.side = self.side.lower()
        self.order_type = self.order_type.lower()
        self.status = self.status.lower()
        assert self.qty >= 0, f"Violation: Negative Qty {self.qty} for Order {self.order_id}"
        
        if self.price is not None:
            assert self.price >= 0, f"Violation: Negative Price {self.price} for Order {self.order_id}"
            
        assert self.side in ['buy', 'sell'], f"Violation: Invalid side {self.side}"

    def __lt__(self, other):
        if self.price is None and other.price is not None:
            return True
        if self.price is not None and other.price is None:
            return False
        
        if self.price is not None and other.price is not None:
            if self.side == 'buy':
                if self.price != other.price:
                    return self.price > other.price
            else:
                if self.price != other.price:
                    return self.price < other.price
        
        return self.timestamp < other.timestamp

@dataclass(slots=True)
class Trade:
    timestamp: float
    price: float
    qty: int
    buyer_id: str
    seller_id: str
    aggressor_side: str
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'price': self.price,
            'qty': self.qty,
            'buyer_id': self.buyer_id,
            'seller_id': self.seller_id,
            'aggressor_side': self.aggressor_side
        }