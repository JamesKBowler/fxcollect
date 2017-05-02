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
        self.fxc = self.fxc_login()
        self.start_scheduler()
        self.live_offers = []
        self.live_data_session()
        logging.basicConfig(filename=s.LIVE_LOG,level=DEBUG)

    def live_data_session(self):
        """
        """
        while True:
            try:
                event = self.live_queue.get(False)
            except queue.Empty:
                sleep(0.0001)            
            else:
                if event.type == 'LIVEDATA':
                    mp.Process(target=DatabaseManager(
                    ).write_data, args=(event,)).start()
                elif event.type == 'GETLIVE':
                    offer = event.offer
                    if offer not in self.live_offers:
                        print("Starting Live : %s" % offer)
                        self.live_offers.append(offer)

    def fxc_login(self):
        """
        Logs into ForexConnectClient and returns a session. 
        """
        while 1:
            try:
                fxc = fx.ForexConnectClient(s.FX_USER, s.FX_PASS,
                                            s.FX_ENVR, s.URL
                )
                if fxc.is_connected() == True:
                    print("Live login sucess")
                    break
            except RuntimeError:
                print("Live login failed - retrying")
                sleep(0.1)
                
        return fxc
     
    def start_scheduler(self):
        """
        APS Scheduler Jobs
        """
        executors = {'processpool': ProcessPoolExecutor(100)
        }
        job_defaults = {
            'coalesce': True,
            'max_instances': 50,
            'misfire_grace_time' : 5
        }
        sched = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
        sched.add_job(self.get_live, 'cron', minute='0-59', args=['m1'])
        sched.add_job(self.get_live, 'cron', minute='0,5,10,15,20,25,30,35,40,45,50,55', args=['m5'])
        sched.add_job(self.get_live, 'cron', minute='0,15,30,45', args=['m15'])
        sched.add_job(self.get_live, 'cron', minute='0,30', args=['m30'])
        sched.add_job(self.get_live, 'cron', hour='0-23', args=['H1'])
        sched.add_job(self.get_live, 'cron', hour='0,2,4,6,8,10,12,14,16,18,20,22', args=['H2'])
        sched.add_job(self.get_live, 'cron', hour='0,4,8,12,16,20', args=['H4'])
        sched.add_job(self.get_live, 'cron', hour='0,8,16', args=['H8'])
        sched.add_job(self.get_live, 'cron', hour='0', args=['D1'])
        sched.add_job(self.get_live, 'cron', day_of_week='sun',hour='17', args=['W1'])
        sched.add_job(self.get_live, 'cron', day='1', hour='17', args=['M1'])
        sched.start()

    def get_live(self, time_frame):
        """
        """
        if self.live_offers != []:
            for offer in self.live_offers:
                db_date = DatabaseManager().return_date(offer, time_frame) 
                fm_date = db_date + datetime.timedelta(minutes = 1)
                tdn = datetime.datetime.now()
                to_date = tdn.replace(second=00, microsecond=00)
                logging.debug("!!] Live Calling dates  : %s From %s : To %s" % (offer, fm_date, to_date))
                data = self.fxc.get_historical_prices(str(offer), fm_date,
                       to_date, str(time_frame)
                )
                data = [d.__getstate__()[0] for d in data]
                data = [x for x in data if db_date not in x.values()]
                if data != []:
                    self.live_queue.put(LiveDataEvent(
                    data, offer, time_frame))

                del data
