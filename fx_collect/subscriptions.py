from .event import EventType, DataEvent
from .offer import Offer
from .settings import JSON_DIR
from termcolor import cprint

import os
import json


class Subscriptions(object):
    def __init__(
        self, init_offers, init_signals,
        offer_broker, price_broker, database_handler
    ):
        self.ob = offer_broker
        self.pb = price_broker
        self.db = database_handler
        self.subscriptions = {}
        self.closed = []
        self.signals = init_signals
        self.jobs = []
        for offer in init_offers:
            self.subscribe(offer)

    def subscribe(self, offer):
        if offer not in self.subscriptions:
            passport = self.ob.get_passport(offer)
            status = self.ob.get_status([offer])[offer]
            broker_name = self.ob.broker
            timestamp, market_status = status
            timeframes, pointsize, contract = passport
            market_open = self.pb.get_open_datetime(offer)
            offer_attribs = Offer(
                broker_name, offer,
                timeframes, market_open, 
                pointsize,
                self.pb._fm_ole(0.0),
                contract
            )
            self.db.create(offer, timeframes)
            self.subscriptions[offer] = offer_attribs
            for timeframe in timeframes:
                fin_bar = self.signals[timeframe]
                dtx = self.db.extremity_dates(offer, timeframe)
                dtfm = self.pb._fm_ole(0.0)
                if dtx:  # Dates found
                    dtto = dtx[0] # Lowest Date
                else:  # No dates
                    dtto = fin_bar['fin']
                self.append_event(
                    -2, offer, timeframe, dtfm, dtto)
                self.subscriptions[offer].update_datetime(
                    timeframe, dtfm, dtto
                )
            cprint("{}: Subscribed".format(offer), 'magenta')

        else:
            print("{} already in Subscriptions".format(offer))

    def record_signal(
        self, finished_bar, current_bar, next_bar, timeframe
    ):
        self.signals[timeframe] = {
            'fin': finished_bar,
            'cur': current_bar,
            'nxt': next_bar,
        }

    def check_subscription(self):
        for offer in self.subscriptions:
            sub = self.subscriptions[offer]
            for timeframe in sub.timeframes:
                signal = self.signals[timeframe]['fin']
                current_bar = self.signals[timeframe]['cur']
                if sub.signal_valid(signal, current_bar, timeframe):
                    jobno, dtfm = sub.return_job(timeframe)
                    self.append_event(
                        jobno, offer, timeframe, dtfm, current_bar)

    def append_event(self, jobno, offer, timeframe, dtfm, dtto):
        self.subscriptions[offer].mark_as_busy(timeframe, True)
        data_event = DataEvent(
            jobno, offer, timeframe,
            dtfm,
            dtto
        )
        self.jobs.append(data_event)
    
    def response(self, jobno, offer, timeframe):
        sub = self.subscriptions[offer]
        # Start and end database dates
        db_min, db_max = self.db.extremity_dates(offer, timeframe)
        sub.update_datetime(timeframe, db_min, db_max)
        # Current signal
        signal = self.signals[timeframe]['fin']
        current_bar = self.signals[timeframe]['cur']
        sub.mark_as_busy(timeframe, False)
        if jobno >= 0:
            if db_max >= signal:
                # Complete
                sub.update_job_number(timeframe, jobno)
            else:
                # Re-send job
                if sub.signal_valid(signal, current_bar, timeframe):
                    self.append_event(
                        jobno, offer, timeframe, db_max, current_bar)
        else:
            if jobno == -2:
                if db_max < signal:
                    # -1 job will perform first data catchup
                    self.append_event(
                        -1, offer, timeframe, db_max, current_bar)
                sub.update_job_number(timeframe, jobno)

            elif jobno == -1:
                if db_max < signal:
                    # 0 job will perform second data catchup before going live
                    self.append_event(
                        0, offer, timeframe, db_max, current_bar)
                sub.update_job_number(timeframe, jobno)

    def update_status(self):
        offers_dict = self.ob.get_status(self.subscriptions)
        for o in offers_dict:
            new = offers_dict[o]
            sub = self.subscriptions[o]
            if (
                new['timestamp'] > sub.timestamp or
                new['status'] != sub.status
            ):
                if sub.status == 'C' and new['status'] == 'O':
                    # Market has just opened
                    sub.market_open = self.pb.get_open_datetime(o)
                bid, ask = self.ob.get_current_bid_ask(o)
                if bid not None and ask not None:
                    sub.update_offer(
                        new['timestamp'], new['status'], bid, ask
                    )
                    self.save_update(o)
                
    def save_update(self, offer, save_to_json=True):
        """
        Saves an update to a JSON file, which can be later accessed
        from another back-testing or live-trading platform.
        """
        json_dir = os.path.join(
            JSON_DIR, "{0}.json".format(offer.replace('/','')))
        if save_to_json:
            snapshot = self.subscriptions[offer].create_snapshot()
            with open(json_dir, 'w') as f:
                json.dump(snapshot, f)
