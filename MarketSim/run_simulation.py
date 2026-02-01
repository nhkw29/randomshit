import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from engine.matching_engine import MatchingEngine
from engine.event_loop import EventLoop
from agents.agents import RandomTrader, MarketMaker
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
    
    np.random.seed(42)
    
    agents = []
    for i in range(noise_count):
        agents.append(RandomTrader(f"NT_{i}"))
    for i in range(mm_count):
        agents.append(MarketMaker(f"MM_{i}"))
    
    def background_step():
        fv_process = FairvalueProcess()
        current_fv = fv_process.step(1.0)
        agent = random.choice(agents)
        snap = order_book.get_snapshot()
        snap['fair_value'] = current_fv
        intent = agent.act(snap)

        if intent and intent['type']=='PLACE_LIMIT':
            order = Order(
                agent_id=intent['agent_id'],
                side=intent['side'],
                price=intent['price'],
                qty=intent['qty'],
                order_type='limit',
                timestamp=None
            )
            orders = order

        if not isinstance(orders, list):
            orders = [orders]
        for order in orders:
            order.timestamp = loop.current_time
            order_book.add_order(order)
        
        lambda_rate = 10
        arrival_delay = np.random.exponential(1/lambda_rate)
        loop.schedule(arrival_delay, background_step)

    loop.schedule(0, background_step)
    
    def record_tick():
        recorder.record_snapshot(order_book, loop.current_time)
        loop.schedule(1.0, record_tick)
    
    loop.schedule(1.0, record_tick)
    loop.run_until(1800.0)
    
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
