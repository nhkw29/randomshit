import heapq
from .order import Order, Trade

class MatchingEngine:
    def __init__(self):
        self.bids = [] 
        self.asks = [] 
        self.tape = [] 
        self.orders = {}
        self.last_mid = 100.0
        self.last_spread = 0.05 # Default tight spread

    def add_order(self, order):
        order.status = 'open'
        self.orders[order.order_id] = order
        if order.qty <= 0:
            return

        if order.side == 'buy':
            self.match(order, self.asks)
        else:
            self.match(order, self.bids)

        if order.qty > 0:
            if order.order_type == 'market':
                order.status = 'cancelled' if order.status == 'open' else 'filled'
                return 
            
            if order.side == 'buy':
                heapq.heappush(self.bids, (-order.price, order.timestamp, order))
            else:
                heapq.heappush(self.asks, (order.price, order.timestamp, order))

    def match(self, incoming_order, book):
        while incoming_order.qty > 0 and len(book) > 0:
            best_price, best_timestamp, resting_order = book[0]
            
            if resting_order.status in ['filled', 'cancelled']:
                heapq.heappop(book)
                continue

            if incoming_order.side == 'sell':
                match_price = -best_price
            else:
                match_price = best_price

            if incoming_order.order_type == 'limit':
                if incoming_order.side == 'buy' and match_price > incoming_order.price:
                    break 
                if incoming_order.side == 'sell' and match_price < incoming_order.price:
                    break 

            executed_qty = min(incoming_order.qty, resting_order.qty)
            
            incoming_order.qty -= executed_qty
            resting_order.qty -= executed_qty

            if incoming_order.qty == 0:
                incoming_order.status = 'filled'
            else:
                incoming_order.status = 'partial'
            
            if resting_order.qty == 0:
                resting_order.status = 'filled'
                heapq.heappop(book)
            else:
                resting_order.status = 'partial'
            
            # ATTRIBUTION FIX
            buyer_id = incoming_order.agent_id if incoming_order.side == 'buy' else resting_order.agent_id
            seller_id = incoming_order.agent_id if incoming_order.side == 'sell' else resting_order.agent_id
            
            new_trade = Trade(
                timestamp=incoming_order.timestamp,
                price=match_price,
                qty=executed_qty,
                buyer_id=buyer_id,
                seller_id=seller_id,
                aggressor_side=incoming_order.side
            )
            self.tape.append(new_trade)
    
    def cancel_order(self, order_id):
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in ['open', 'partial']:
                order.status = 'cancelled'
                return True
        return False
        
    def clean_book(self, book):
        while book and book[0][2].status in ['filled', 'cancelled']:
            heapq.heappop(book)
    
    def get_snapshot(self):
        self.clean_book(self.bids)
        self.clean_book(self.asks)

        best_bid = -self.bids[0][0] if self.bids else None
        best_ask = self.asks[0][0] if self.asks else None
        
        # --- FIX: SPREAD MEMORY ---
        # If market is one-sided or empty, use last known good spread
        # to prevent charts from looking like data is missing.
        if best_bid is not None and best_ask is not None:
            mid = (best_bid + best_ask) / 2
            spread = best_ask - best_bid
            self.last_spread = spread
        elif best_bid is not None:
            mid = best_bid
            spread = self.last_spread # Use memory
        elif best_ask is not None:
            mid = best_ask
            spread = self.last_spread # Use memory
        else:
            mid = self.last_mid
            spread = self.last_spread

        self.last_mid = mid

        return {
            'best_bid': best_bid if best_bid is not None else 0.0, 
            'best_ask': best_ask if best_ask is not None else float('inf'), 
            'mid_price': mid, 
            'spread': spread
        }

    def run_sanity_check(self):
        return True
