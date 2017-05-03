from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
import Queue as queue
import settings as s
from event import GetLiveEvent
import logging
from logging import DEBUG

class LiveEventTimer(object):
    """
    Creates time based event for collecting FXCM data.
    
    Information on this API
    https://apscheduler.readthedocs.io/en/latest/
    https://github.com/agronholm/apscheduler/
    """
    def __init__(self, live_queue):
        """
        """
        logging.basicConfig(filename=s.LIVE_LOG,level=DEBUG)
        self.live_queue = live_queue        
     
    def _start_scheduler(self):
        """
        APS Scheduler Jobs
        """
        executors = {'processpool': ProcessPoolExecutor(100)
        }
        job_defaults = {
            'coalesce': True,
            'max_instances': 50,
            'misfire_grace_time' : 20
        }
        sched = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
        sched.add_job(self._put_event, 'cron', minute='0-59', args=['m1'])
        sched.add_job(self._put_event, 'cron', minute='0,5,10,15,20,25,30,35,40,45,50,55', args=['m5'])
        sched.add_job(self._put_event, 'cron', minute='0,15,30,45', args=['m15'])
        sched.add_job(self._put_event, 'cron', minute='0,30', args=['m30'])
        sched.add_job(self._put_event, 'cron', hour='0-23', args=['H1'])
        sched.add_job(self._put_event, 'cron', hour='0,2,4,6,8,10,12,14,16,18,20,22', args=['H2'])
        sched.add_job(self._put_event, 'cron', hour='0,4,8,12,16,20', args=['H4'])
        sched.add_job(self._put_event, 'cron', hour='0,8,16', args=['H8'])
        sched.add_job(self._put_event, 'cron', hour='0', args=['D1'])
        sched.add_job(self._put_event, 'cron', day_of_week='sun',hour='17', args=['W1'])
        sched.add_job(self._put_event, 'cron', day='1', hour='17', args=['M1'])
        sched.start()

    def _put_event(self, time_frame):
        self.live_queue.put(GetLiveEvent(time_frame))
        
    def start(self):
        print("Time Keeper Started")
        self._start_scheduler()
