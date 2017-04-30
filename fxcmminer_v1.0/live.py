from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from db_manager import DatabaseManager
import time
import datetime
import forexconnect as fx
import settings as s
from event import LiveDataEvent
import re

class LiveDataMiner(object):
    """
    Creates time based event for collecting FXCM data.

    Information on this API
    https://apscheduler.readthedocs.io/en/latest/
    https://github.com/agronholm/apscheduler/
    """
    def __init__(self, events_queue, event):
        while True:
            try:
                self.fxc = fx.ForexConnectClient(str(s.FX_USER),
                                                 str(s.FX_PASS),
                                                 str(s.FX_ENVR))
                if self.fxc.is_connected() == True:
                    break
            except RuntimeError:
                pass

        self.events_queue = events_queue
        self.offer = event.offer
        self.executors = {'processpool': ProcessPoolExecutor(100)
        }

        self.job_defaults = {
            'coalesce': True,
            'max_instances': 12
        }
        self.sched = BackgroundScheduler(executors=self.executors)

        self.sched.add_job(self.min_1,'cron', minute='0-59')
        self.sched.add_job(self.min_5, 'cron', minute='0,5,10,15,20,25,30,35,40,45,50,55')
        self.sched.add_job(self.min_15, 'cron', minute='0,15,30,45')
        self.sched.add_job(self.min_30, 'cron', minute='0,30')
        self.sched.add_job(self.hour_1, 'cron', hour='0-23')
        self.sched.add_job(self.hour_2, 'cron', hour='0,2,4,6,8,10,12,14,16,18,20,22')
        self.sched.add_job(self.hour_4, 'cron', hour='0,4,8,12,16,20')
        self.sched.add_job(self.hour_8, 'cron', hour='0,8,16')
        self.sched.add_job(self.day_1, 'cron', hour='0')
        self.sched.add_job(self.week_1, 'cron', day_of_week='sun',hour='17')
        self.sched.add_job(self.month_1, 'cron', day='1', hour='17')

    def min_1(self):
        tf = 'm1'
        p = 1
        self.get_live(tf, p, self.fxc)

    def min_5(self):
        tf = 'm5'
        p = 2
        self.get_live(tf, p, self.fxc)

    def min_15(self):
        tf = 'm15'
        p = 3
        self.get_live(tf, p, self.fxc)

    def min_30(self):
        tf = 'm30'
        p = 4
        self.get_live(tf, p, self.fxc)

    def hour_1(self):
        tf = 'H1'
        p = 5
        self.get_live(tf, p, self.fxc)

    def hour_2(self):
        tf = 'H2'
        p = 6
        self.get_live(tf, p, self.fxc)

    def hour_4(self):
        tf = 'H4'
        p = 7
        self.get_live(tf, p, self.fxc)

    def hour_8(self):
        tf = 'H8'
        p = 8
        self.get_live(tf, p, self.fxc)

    def day_1(self):
        tf = 'D1'
        p = 9
        self.get_live(tf, p, self.fxc)

    def week_1(self):
        tf = 'W1'
        p = 10
        self.get_live(tf, p, self.fxc)

    def month_1(self):
        tf = 'M1'
        p = 11
        self.get_live(tf, p, self.fxc)

    def get_live(self, time_frame, priority, fxc):
        """
        """
        fm_date = DatabaseManager().return_date(self.offer, time_frame)
        fm_date = fm_date + datetime.timedelta(minutes = 1)
        to_date = datetime.datetime.now()
        instrument = self.offer
        try:
            data = fxc.get_historical_prices(
                   str(instrument), fm_date,
                   to_date, str(time_frame))
            data = [d.__getstate__()[0] for d in data]
        except (KeyError, IndexError):
            data = []

        if data != []:
            self.events_queue.put(LiveDataEvent(
            data, instrument, time_frame))

        del data

    def start_timers(self):
        self.sched.start()
