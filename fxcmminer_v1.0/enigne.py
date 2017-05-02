from db_manager import DatabaseManager
from  historical import HistoricalCollector
from live import LiveDataMiner
from fxscout import Scout
import forexconnect as fx
import settings
import multiprocessing as mp
import Queue as queue
from time import sleep


class Engine(object):
    def __init__(self):
        self.hist_queue = mp.Queue(100)
        self.live_queue = mp.Queue(600)

    def _hist_mining(self):
        """
        Collect events from the Queue
        """
        while True:
            try:
                event = self.hist_queue.get(False)
            except queue.Empty:
                sleep(0.0001)            
            else:
                if event.type == 'HISTDATA':
                    mp.Process(target=DatabaseManager(
                    ).write_data, args=(event,)).start()

                elif event.type == 'DBREADY':
                    mp.Process(target=HistoricalCollector(
                    ).historical_prices, args=(self.hist_queue,
                                               self.live_queue, event,)
                                               ).start()                    
                elif event.type == 'OFFER':
                    mp.Process(target=DatabaseManager(
                    ).database_check, args=(self.hist_queue, event,)
                                            ).start()

    def start(self):
        print('Engines Running..')
        Scout(self.hist_queue).start()
        mp.Process(target=self._hist_mining).start()
        LiveDataMiner(self.live_queue).start()


if __name__ == "__main__":
    Engine().start()
