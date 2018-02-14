from .event import EventType
from .broker.fxcm import FXCMBrokerOffers
from .broker.fxcm import FXCMBrokerHistory
from .database.mariadb import Database
from .subprocess_engine import SubprocessEngine
from .signals.time_signals import TimeSignals
from .subscription_handler import SubscriptionHandler
from .settings import DB_HOST, DB_USER, DB_PASS, FX_USER, FX_PASS, FX_ENVR, URL

import time
import queue
from datetime import datetime

class CollectionSession(object):
    def __init__(
        self, config, offers, events_queue, end_session_time=None,
        offer_broker=None, price_broker=None, database_handler=None,
        subprocess_engine=None, subscription_handler=None,
        time_handler=None
    ):
        self.config = config
        self.offers = offers
        self.events_queue = events_queue
        self.offer_broker = offer_broker # << offers table is CPU intensive
        self.price_broker = price_broker # < this does not have the offers table
        self.database_handler = database_handler
        self.subprocess_engine = subprocess_engine
        self.subscription_handler = subscription_handler
        self.time_handler = time_handler
        self._config_session()
        self.cur_time = datetime.utcnow()
        self._live_collection = True

    def _config_session(self):
        if self.database_handler is None:
            self.database_handler = Database(
                'fxcm', DB_HOST, DB_USER, DB_PASS
            )

        if self.offer_broker is None:
            self.offer_broker = FXCMBrokerOffers(
                FX_USER, FX_PASS, FX_ENVR, URL
            )
        if self.price_broker is None:
            self.price_broker = FXCMBrokerHistory(
                FX_USER, FX_PASS, FX_ENVR, URL
            )

        self.start_date, self.end_date = self.price_broker.current_tradingweek()

        if self.time_handler is None:
            self.time_handler = TimeSignals(
                self.events_queue,
                self.offer_broker.supported_timeframes,
                self.start_date,
                self.end_date
            )

        init_signals = self.time_handler.init_signals

        if self.subprocess_engine is None:
            self.subprocess_engine = SubprocessEngine(
                self.config,
                self.events_queue
            )
        if self.subscription_handler is None:
            self.subscription_handler = SubscriptionHandler(
                self.events_queue,
                self.offers,
                init_signals,
                self.offer_broker,
                self.price_broker,
                self.database_handler
            )

    def _continue_loop_condition(self):
        self.cur_time = self.time_handler.cur_time
        if self._live_collection:
            return self.cur_time < self.end_date
        else:
            return True

    def _run_session(self):
        print("Running Session...")
        while self._continue_loop_condition():
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
                self._shutdown()

    def _shutdown(self):
        self.offer_broker._logout()
        self.price_broker._logout()
        self.subprocess_engine.kill_process()
        
    def start_collection(self):
        self._run_session()
        self._shutdown()
        return
