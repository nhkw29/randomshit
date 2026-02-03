import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from engine.matching_engine import MatchingEngine
from engine.event_loop import EventLoop
from agents.agents import MarketMaker, NoiseTrader, MomentumTrader
from analytics.tape import Tape
from analytics.snapshots import SnapshotRecorder
from analytics.plots import MarketPlots
import random
from engine.order import Order

def run_scenario(pdf, scenario_name, noise_count, mm_count, mom_count):
    order_book = MatchingEngine()
    loop = EventLoop()
    tape = Tape()
    recorder = SnapshotRecorder()
    
    # --- FIX 1: SIGMA = 0.05 (Prevents Market Crash) ---
    fv_process = FairvalueProcess(initial_value=100.0, mu=0.0, sigma=0.05)
    
    np.random.seed(42)
    
    agents = []
    for i in range(noise_count):
        agents.append(NoiseTrader(f"NT_{i}"))
    for i in range(mm_count):
        # Increased inventory limit so MMs stay active
        agents.append(MarketMaker(f"MM_{i}", inventory_limit=1000))
    for i in range(mom_count):
        agents.append(MomentumTrader(f"MOM_{i}"))
    
    def background_step():
        lambda_rate = 10
        arrival_delay = np.random.exponential(1/lambda_rate)
        current_fv = fv_process.step(arrival_delay)
        
        # State Sync
        for trade in order_book.tape:
            for agent in agents:
                if trade.buyer_id == agent.agent_id:
                    agent.inventory += trade.qty
                    agent.balance -= trade.qty * trade.price
                elif trade.seller_id == agent.agent_id:
                    agent.inventory -= trade.qty
                    agent.balance += trade.qty * trade.price
        order_book.tape.clear()

        agent = random.choice(agents)
        snap = order_book.get_snapshot()
        
        if isinstance(agent, NoiseTrader):
            snap['fair_value'] = current_fv
        else:
            snap.pop('fair_value', None)
        
        action = agent.act(snap)
        
        if action:
            intents = [action] if isinstance(action, dict) else action
            for item in intents:
                if isinstance(item, dict):
                    order_type = item['type'].split('_')[1].lower()
                    new_order = Order(
                        agent_id=item['agent_id'],
                        side=item['side'],
                        qty=item['qty'],
                        price=item.get('price'),
                        order_type=order_type,
                        timestamp=loop.current_time
                    )
                    order_book.add_order(new_order)
                else:
                    item.timestamp = loop.current_time
                    order_book.add_order(item)

        loop.schedule(arrival_delay, background_step)

    # --- FIX 2: WARM-UP LOOP (Prevents Start-Up Spike) ---
    print(f"  > Warming up {scenario_name}...")
    for _ in range(200): 
        mm_agents = [a for a in agents if isinstance(a, MarketMaker)]
        if not mm_agents: break
        
        agent = random.choice(mm_agents)
        snap = order_book.get_snapshot()
        # Seed the book if empty
        if snap['mid_price'] == 100.0 and snap['spread'] == 0:
            snap['mid_price'] = 100.0
            snap['spread'] = 1.0

        action = agent.act(snap)
        if action:
            for item in action:
                o = Order(item['agent_id'], item['side'], item['qty'], item['price'])
                order_book.add_order(o)

    loop.schedule(0, background_step)
    
    def record_tick():
        recorder.record_snapshot(order_book, loop.current_time)
        loop.schedule(1.0, record_tick)
    
    loop.schedule(1.0, record_tick)
    loop.run_until(3600.0)
    
    plotter = MarketPlots(recorder, tape)
    plotter.generate_scenario_report(pdf, scenario_name)

class FairvalueProcess:
    def __init__(self, initial_value=100.0, mu=0.0, sigma=1.0):
        self.current_value = initial_value
        self.mu = mu
        self.sigma = sigma
    
    def step(self, dt):
        dW = np.random.normal(0, np.sqrt(dt))
        self.current_value *= np.exp((self.mu - 0.5 * self.sigma**2) * dt + self.sigma * dW)
        return self.current_value

def main():
    with PdfPages('simulation_report.pdf') as pdf:
        scenarios = [
            ("Scenario A: Noise Only", 100, 0, 0),
            ("Scenario B: Noise + Market Makers", 80, 20, 0),
            ("Scenario C: Noise + Momentum", 80, 0, 20)
        ]
        
        for name, n, mm, mom in scenarios:
            run_scenario(pdf, name, n, mm, mom)

if __name__ == "__main__":
    main()
