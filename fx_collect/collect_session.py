from .event import EventType
from .broker.fxcm.session import FXCMBroker
from .database.mariadb import Database
from .subprocess_engine import SubprocessEngine
from .signals.time_signals import TimeSignals
from .subscription_handler import SubscriptionHandler

import time
import queue
from datetime import datetime

class CollectionSession(object):
    def __init__(
        self, events_queue, offers=None, end_session_time=None,
        broker=None, database_handler=None,
        subprocess_engine=None, subscription_handler=None,
        time_handler=None
    ):
        self.offers = offers
        self.events_queue = events_queue
        self.broker = broker
        self.database_handler = database_handler
        self.subprocess_engine = subprocess_engine
        self.subscription_handler = subscription_handler
        self.time_handler = time_handler
        self._config_session()
        self.cur_time = datetime.utcnow()
        self._live_collection = False

    def _config_session(self):
        if self.broker is None:
            self.broker = FXCMBroker(
                offers_table=True,
                market_data=True,
                trading=False
        )
            
        if self.database_handler is None:
            self.database_handler = Database(self.broker.whoami())

        # Define a starting point and end point for the
        # current week.
        dates = self.broker.market_data.current_tradingweek()
        self.start_date, self.end_date = dates
        print("Week Start: {0} End: {1}".format(
            self.start_date, self.end_date)
        )
        if self.offers is None:
            self.offers = self.broker.offers_table.get_offers()

        if self.time_handler is None:
            self.time_handler = TimeSignals(
                self.events_queue,
                self.start_date,
                self.end_date
            )
        init_signals = self.time_handler.init_signals
        if self.subprocess_engine is None:
            self.subprocess_engine = SubprocessEngine(
                self.events_queue
            )
        if self.subscription_handler is None:
            self.subscription_handler = SubscriptionHandler(
                self.events_queue,
                self.offers,
                init_signals,
                self.broker,
                self.database_handler
            )

    def _continue_loop_condition(self):
        self.cur_time = self.time_handler.cur_time
        if self._live_collection:
            if self.cur_time < self.end_date:
                return True
            else:
                return self._shutdown()
        else:
            return True

    def _run_session(self):
        print("Running Session...")
        while self._continue_loop_condition():
            #print(self.events_queue.qsize(),self.cur_time, self.end_date)
            try:
                self.time_handler.generate_signals()
                try:
                    event = self.events_queue.get(False)
                except queue.Empty:
                    self.subscription_handler.on_status()
                    time.sleep(0.05)
                else:
                    if event is not None:
                        if event.type == EventType.SIGNAL:
                            self.subscription_handler.on_signal(event)
                        elif event.type == EventType.GETDATA:
                            self.subprocess_engine.on_collect(event)
                        elif event.type == EventType.RESPONSE:
                            self.subscription_handler.on_response(event)
                        else:
                            raise NotImplemented(
                                "Unsupported event.type {}".format(event.type)
                            )
            except KeyboardInterrupt:
                self.broker.offers_table._logout_session()
                self.broker.market_data._logout_session()
                time.sleep(5)

    def _shutdown(self):
        self.broker.offers_table._logout_session()
        self.broker.market_data._logout_session()
        self.subprocess_engine.kill_process()
        return False
        
    def start_collection(self):
        self._run_session()
        return