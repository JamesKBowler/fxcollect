from db_manager import DatabaseManager
from historical import HistoricalCollector
from live import LiveDataMiner
from fxscout import Scout
import forexconnect as fx
import settings
import multiprocessing as mp
import Queue as queue
from time import sleep


class Engine(object):
    def __init__(self):
        self.events_queue = mp.Queue(100)

    def _mining(self):
        """
        Collect events from the Queue
        """
        Scout(self.events_queue).start()

        while True:
            try:
                event = self.events_queue.get(False)
            except queue.Empty:
                sleep(0.0001)            
            else:
                if event.type == 'LIVEDATA':
                    mp.Process(target=DatabaseManager(
                    ).write_data, args=(event,)).start()
                elif event.type == 'GETLIVE':
                    mp.Process(target=LiveDataMiner(
                    self.events_queue, event).start_timers()).start()
                elif event.type == 'HISTDATA':
                    mp.Process(target=DatabaseManager(
                    ).write_data, args=(event,)).start()
                elif event.type == 'DBREADY':
                    mp.Process(target=HistoricalCollector(
                    ).historical_prices, args=(self.events_queue, event,)).start()                    
                elif event.type == 'OFFER':
                    mp.Process(target=DatabaseManager(
                    ).database_check, args=(self.events_queue, event,)).start()

    def start(self):
        self._mining()


if __name__ == "__main__":
    Engine().start()
