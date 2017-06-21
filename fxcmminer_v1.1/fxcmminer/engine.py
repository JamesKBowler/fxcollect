import multiprocessing as mp
import Queue as queue
from time import sleep
from cleaning.laundry import DataCleaner
from fxcm.fxscout import Scout
from fxcm.historical import HistoricalCollector
from database.base import DatabaseManager
from fxcm.live import LiveCollector
from livetimings.timekeeper import LiveEventTimer


class HistEngine(object):
    """
    Encapsulates all Historical data collection logic.
    """
    def _historical(
        self, hist_queue, live_queue, hist_collector,
        data_cleaner, database_manager
    ):
        """
        An infinate loop collecting events from the Queue.
        """
        while True:
            try:
                event = hist_queue.get(False)
            except queue.Empty:
                sleep(0.01)            
            else:
                if event.type == 'HISTDATA':
                    mp.Process(
                        target=data_cleaner.clean_data,
                        args=(event,)).start()
                elif event.type == 'CLEANED':
                    mp.Process(
                        target=database_manager.write_to_db,
                        args=(event,)).start()
                elif event.type == 'OFFER':
                    mp.Process(
                        target=hist_collector.historical_prices,
                        args=(event,)).start()
                else:
                    raise NotImplemented("Unsupported Event : %s" % event.type)


class LiveEngine(object):
    """
    Encapsulates all Live data collection logic.
    """
    def _store_live_offers(self, event):
        """
        Stores a list of offers ready for live data collection
        """
        if event.offer not in self.live_offers:
            print("[oo] LIVE  | Started  : %s" % event.offer)
            self.live_offers.append(event.offer)        

    def _start_live(self, event, live_miner):
        """
        Live data collection manager. This method can be adjusted 
        to be more aggresive for each login. For example the faster your
        internet connection the more aggressive you can be.
        
        Current setting is 15... lower is more aggressive and can lead
        to responce timeout errors with FXCM servers.
        """
        offers = []
        iters = 0
        live_groups = [o for o in self.live_offers]
        print('[!!] TIME  | Trigger  : %s' % event.time_frame)
        for offer in live_groups:
            iters += 1
            offers.append(offer)
            if (len(offers) == 15 or
               iters == len(live_groups)
            ):
                mp.Process(
                    target=live_miner.live_prices, 
                    args=(offers, event.time_frame,)).start()
                offers = []
             
    def _live(
        self, live_queue, live_miner, data_cleaner,
        database_manager
    ):
        """
        An infinate loop collecting events from the Queue.
        """
        self.live_offers = []
        while True:
            try:
                event = live_queue.get(False)
            except queue.Empty:
                sleep(0.01)
            else:
                if event.type == 'LIVEDATA':
                    mp.Process(
                        target=data_cleaner.clean_data,
                        args=(event,)).start()
                elif event.type == 'CLEANED':
                    mp.Process(
                        target=database_manager.write_to_db,
                        args=(event,)).start()
                elif event.type == 'LASTDATE':
                    self._store_last_date(event)
                elif event.type == 'GETLIVE':
                    if self.live_offers != []:
                        self._start_live(event, live_miner)
                elif event.type == 'LIVEREADY':
                    self._store_live_offers(event)
                else:
                    raise NotImplemented("Unsupported Event : %s" % event.type)


def start():
    hist_queue = mp.Queue(100)
    live_queue = mp.Queue(600)
    time_frames = [
        'M1','W1','D1','H8','H4','H2','H1','m30','m15','m5','m1'
    ]
    print('[:)] Engines Running..')
    mp.Process(target=HistEngine(
        )._historical, args=(hist_queue, live_queue,
                             HistoricalCollector(hist_queue, live_queue),
                             DataCleaner(hist_queue), 
                             DatabaseManager(),)).start()
    mp.Process(target=LiveEngine(
        )._live, args=(live_queue,
                       LiveCollector(live_queue),
                       DataCleaner(live_queue),
                       DatabaseManager(),)).start()
    LiveEventTimer(live_queue).start()
    Scout(hist_queue, time_frames).run()

if __name__ == "__main__":
    start()
