from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from db_manager import DatabaseManager
import multiprocessing as mp
import Queue as queue
from time import sleep
import time
import datetime
import forexconnect as fx
import settings as s
from event import LiveDataEvent
import re
import logging
from logging import DEBUG

class LiveDataMiner(object):
    """
    Creates time based event for collecting FXCM data.
    
    Information on this API
    https://apscheduler.readthedocs.io/en/latest/
    https://github.com/agronholm/apscheduler/
    """
    def __init__(self, live_queue):
        """
        """
        self.live_queue = live_queue

    def _fxc_login(self):
        """
        Logs into ForexConnectClient and returns a session. 
        """
        while 1:
            try:
                fxc = fx.ForexConnectClient(s.FX_USER, s.FX_PASS,
                                            s.FX_ENVR, s.URL
                )
                if fxc.is_connected() == True:
                    break
            except RuntimeError:
                sleep(0.1)

        return fxc

    def _get_live(self, event, fxc, live_offers):
        """
        """
        time_frame = event.time_frame
        if live_offers != []:
            for offer in live_offers:
                db_date = DatabaseManager().return_date(offer, time_frame) 
                fm_date = db_date + datetime.timedelta(minutes = 1)
                tdn = datetime.datetime.now()
                to_date = tdn.replace(second=00, microsecond=00)
                data = fxc.get_historical_prices(str(offer), fm_date,
                       to_date, str(time_frame)
                )
                data = [d.__getstate__()[0] for d in data]
                data = [x for x in data if db_date not in x.values()]
                if data != []:
                    self.live_queue.put(LiveDataEvent(
                    data, offer, time_frame))

                del data

    def _live_data_session(self, fxc):
        """
        """
        live_offers = []
        while True:
            try:
                event = self.live_queue.get(False)
            except queue.Empty:
                sleep(0.1)            
            else:
                if event.type == 'LIVEDATA':
                    mp.Process(target=DatabaseManager(
                    ).write_data, args=(event,)).start()
                elif event.type == 'GETLIVE':
                    mp.Process(self._get_live(event, fxc, live_offers)).start()
                elif event.type == 'LIVEREADY':
                    if event.offer not in live_offers:
                        print("[oo] Live Started %s" % event.offer)
                        live_offers.append(event.offer)
                    
    def live_mine(self):
        self._live_data_session(self._fxc_login())
