from fx_collect.utils.date_utils import fm_ole
from .event import EventType, DataEvent, ResponseEvent
from .offer import Offer
from .settings import JSON_DIR
from termcolor import cprint
import os
import json
import time

class Subscriptions(object):
    """
    
    """
    def __init__(
        self, init_offers, init_signals,
        offer_broker, price_broker, database_handler, events_queue
    ):
        """
        
        """
        self.events_queue = events_queue
        self.ob = offer_broker
        self.pb = price_broker
        self.db = database_handler
        self.subscriptions = {}
        self.signals = init_signals
        for offer in init_offers:
            self.subscribe(offer)

    def _place_event_into_queue(
        self, jobno, offer, timeframe, dtfm, dtto
    ):
        """
        
        """
        self.subscriptions[offer].mark_as_busy(timeframe, True)
        data_event = DataEvent(
            jobno, offer, timeframe,
            dtfm,
            dtto
        )
        self.events_queue.put(data_event)

    def _penalty_box(self, job, events_queue, pen):
        """
        
        """
        from threading import Thread
        def _sleeper(j, q, pen):
            jobno, offer, time_frame = j
            time.sleep(pen)
            event = ResponseEvent(
                jobno,
                offer,
                time_frame
            )
            q.put(event)

        _t = Thread(target=_sleeper,
                args = (job, events_queue, pen,))
        _t.daemon = True
        _t.start()

    def subscribe(self, offer):
        """
        
        """
        if offer not in self.subscriptions:
            # Collect all offer attributes
            passport = self.ob.get_passport(offer)
            status = self.ob.get_status([offer])[offer]
            broker_name = self.ob.whoami
            timestamp, market_status = status
            timeframes, pointsize, contract = passport
            market_open = self.pb.get_open_datetime(offer)
            # Create Offer object
            offer_attribs = Offer(
                broker_name, offer,
                timeframes, market_open, 
                pointsize,
                fm_ole(0.0),
                contract
            )
            # Check is database and tables are created
            self.db.create(offer, timeframes)
            # Add to subscriptions dict
            self.subscriptions[offer] = offer_attribs
            # Create jobs for each time frame.
            # All jobs start from the lowest date
            for timeframe in timeframes:
                fin_bar = self.signals[timeframe]
                dtx = self.db.extremity_dates(offer, timeframe)
                dtfm = fm_ole(0.0)
                if dtx:  # Dates found
                    dtto = dtx[0] # Lowest Date
                else:  # No dates
                    dtto = fin_bar['fin']
                # Create and place event into queue.
                self._place_event_into_queue(
                    -2, offer, timeframe, dtfm, dtto)
                # Initialise date time attributes 
                self.subscriptions[offer].update_datetime(
                    timeframe, dtfm, dtto
                )
            # Confirmation to console
            cprint("{0: <{width}}: Subscribed".format(
                offer, width=9), 'magenta')
        else:
            print("{} already in Subscriptions".format(offer))

    def check_subscription(self):
        """
        
        """
        s = self.subscriptions
        iter_jobs = [(x,y) for x in s for y in s[x].timeframes]
        for offer, timeframe in iter_jobs:
            # Get signal and current bar datetime
            signal = self.signals[timeframe]['fin']
            current_bar = self.signals[timeframe]['cur']
            # Check if the signal is valid
            if s[offer].signal_valid(signal, current_bar, timeframe):
                # Create new job number
                jobno, dtfm = s[offer].return_job(timeframe)
                # Create and place event into queue.
                self._place_event_into_queue(
                    jobno, offer, timeframe, dtfm, current_bar)
            else:
                # Do nothing
                pass

    def _transact_live_data(
        self, jobno, offer, timeframe, sub, db_max, signal, current_bar
    ):
        """
        
        """
        if db_max >= signal:
            # Complete
            sub.update_job_number(timeframe, jobno)
        else:
            # Add penalty
            if sub.penalty(timeframe, clear=False):
                # Clear penalty's
                sub.penalty(timeframe, clear=True)
                # Over 5 penalty mark as "busy" for 50 seconds
                sub.mark_as_busy(timeframe, True)
                # Make sleeper thread
                job = jobno, offer, timeframe
                self._penalty_box(job, self.events_queue, 50)
                # Print out event
                cprint("Type: Penalty: Jobno: {0} Offer: {1} Time Frame: {2}".format(
                    jobno, offer, timeframe), 'cyan')
            else:
                # Re-send job
                if sub.signal_valid(signal, current_bar, timeframe):
                    # Create and place event into queue.
                    self._place_event_into_queue(
                        jobno, offer, timeframe, db_max, current_bar)

    def _transact_historical_data(
        self, jobno, offer, timeframe, sub, db_max, signal, current_bar
    ):
        """
        
        """
        if jobno < 0:
            sub.update_job_number(timeframe, jobno)
            if db_max < signal:
                # Create new job number
                jobno, dtfm = sub.return_job(timeframe)
                # Create and place event into queue.
                self._place_event_into_queue(
                    jobno, offer, timeframe, db_max, current_bar)

    def response(self, jobno, offer, timeframe):
        """
        
        """
        sub = self.subscriptions[offer]
        # Start and end database dates
        db_min, db_max = self.db.extremity_dates(offer, timeframe)
        sub.update_datetime(timeframe, db_min, db_max)
        # Current signal
        signal = self.signals[timeframe]['fin']
        current_bar = self.signals[timeframe]['cur']
        # Remove "busy" flag from Offer.
        sub.mark_as_busy(timeframe, False)
        if jobno >= 0:
            # Live collections
            self._transact_live_data(
                jobno, offer, timeframe, sub,
                db_max, signal, current_bar
            )

        else:
            # Historical collections
            self._transact_historical_data(
                jobno, offer, timeframe, sub,
                db_max, signal, current_bar
            )

    def save_update(self, offer, save_to_json=True):
        """
        Saves an update to a JSON file, which can be later accessed
        from another api.
        """
        json_dir = os.path.join(
            JSON_DIR, "{0}.json".format(offer.replace('/','')))
        if save_to_json:
            snapshot = self.subscriptions[offer].create_snapshot()
            with open(json_dir, 'w') as f:
                json.dump(snapshot, f)

    def update_status(self):
        """
        
        """
        offers_dict = self.ob.get_status(self.subscriptions.keys())
        for o in offers_dict:
            new_timestamp = offers_dict[o]['timestamp']
            new_status = offers_dict[o]['status']
            sub = self.subscriptions[o]
            if (
                new_timestamp > sub.timestamp or
                new_status != sub.status
            ):
                if sub.status == 'C' and new_status == 'O':
                    # Market has just opened
                    sub.market_open = self.pb.get_open_datetime(o)
                bid, ask = self.ob.get_current_bid_ask(o)
                if bid is not None and ask is not None:
                    sub.update_offer(
                        new_timestamp, new_status, bid, ask
                    )
                    self.save_update(o)