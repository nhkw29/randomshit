import heapq

class EventLoop:
    def __init__(self):
        self.current_time = 0.0
        self.event_queue = []
        self.sequence_counter = 0

    def schedule(self, delay, callback,priority=1):
        target_time = self.current_time + delay
        self.sequence_counter += 1
        
        event = (target_time, priority, self.sequence_counter, callback)
        
        heapq.heappush(self.event_queue, event)
    
    def process_next_event(self):
        if not self.event_queue:
            return False
            
        timestamp, priority, _, callback = heapq.heappop(self.event_queue)
        
        self.current_time = timestamp
        
        callback()
        return True

    def run_until(self, max_time):
        
        while self.event_queue:
            next_time = self.event_queue[0][0]
            
            if next_time > max_time:
                break
                
            self.process_next_event()
        self.current_time = max_time