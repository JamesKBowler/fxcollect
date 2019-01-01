# The MIT License (MIT)
#
# Copyright (c) 2017 James K Bowler, Data Centauri Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from fx_collect.utils.date_utils import fm_ole
from .event import EventType, DataEvent, ResponseEvent
from .offer import Offer
from .settings import JSON_DIR, COLLECT_TIMEFRAMES_ONLY
from termcolor import cprint
import os
import json
import time
from traceback import print_exc

class Subscriptions(object):
    """
    Subscriptions is designed to keep track of all offers
    from the broker.
    """
    def __init__(
        self, init_offers, init_signals,
        offer_broker, price_broker, database_handler, events_queue
    ):
        self.events_queue = events_queue
        self.ob = offer_broker
        self.pb = price_broker
        self.db = database_handler
        self.subscriptions = {}
        self.signals = init_signals
        for offer in init_offers:
            self.subscribe(offer)

    def _create_data_event(
        self, jobno, offer, timeframe, dtfm, dtto
    ):
        """
        Mark offer time frame as busy, create and place 
        all DataEvents into the queue.
        """
        # Mark the offers time frame as busy, therefore this
        # time frame will ignore signals.
        self.subscriptions[offer].attribs[timeframe]['busy'] = True
        # Create event
        data_event = DataEvent(
            jobno, offer, timeframe,
            dtfm,
            dtto
        )
        # Put event into queue
        self.events_queue.put(data_event)

    def subscribe(self, offer):
        """
        Adds an offer to the subscriptions dictionary.
        """
        if offer not in self.subscriptions:
            # Collect all offer attributes
            broker_name = self.ob.whoami
            passport = self.ob.get_passport(offer)
            status = self.ob.get_status([offer])[offer]
            market_open = self.pb.get_open_datetime(offer)
            timestamp, market_status = status
            timeframes, pointsize, contract = passport
            if COLLECT_TIMEFRAMES_ONLY:
                timeframes_ = []
                for tf in timeframes:
                    if tf in COLLECT_TIMEFRAMES_ONLY:
                        timeframes_.append(tf)
                timeframes=timeframes_
            # Create Offer object
            offer_attribs = Offer(
                broker_name, offer,
                timeframes, market_open,
                pointsize, fm_ole(0.0),
                contract
            )
            # Check is database and tables are created
            self.db.create(offer, timeframes)
            # Add to subscriptions dict
            self.subscriptions[offer] = offer_attribs
            # Create jobs for each time frame.
            # All jobs start from OLE Zero, to the lowest date
            # in database (if data) or current finished bar.
            for timeframe in timeframes:
                fin_bar = self.signals[timeframe]
                dtx = self.db.extremity_dates(offer, timeframe)
                dtfm = fm_ole(0.0)
                if dtx:  # Dates found
                    dtto = dtx[0] # Lowest Date
                else:  # No dates
                    dtto = fin_bar['fin']
                # Create and place event into queue.
                self._create_data_event(
                    -2, offer, timeframe, dtfm, dtto)
                # Initialise date time attributes (reversed)
                self.subscriptions[offer].attribs[timeframe]['db_min'] = dtto
                self.subscriptions[offer].attribs[timeframe]['db_max'] = dtfm
            # Confirmation to console
            cprint("{0: <{width}}: Subscribed".format(
                offer, width=9), 'magenta')
        else:
            print(
                "Error: {} already in Subscriptions".format(offer)
            )

    def _penalty_box(self, jobno, offer, timeframe, pen=50):
        """
        Data arrives at different times depending on a lot
        of factors. For example sometimes offers
        such as the EUSTX50 will be open but no new data has
        arrived at the exchange. This causes fx_collect to
        aggressively make API calls.
        
        Maybe the guy pushing the buttons is having
        a quick coffee? 

        To avoid this a penalty of 50 seconds is applied
        when over 5 API calls are made and the data is
        returned empty.

        """
        from threading import Thread
        def _sleeper(
            jobno, offer, timeframe,
            events_queue, pen
        ):
            time.sleep(pen)
            event = ResponseEvent(
                jobno,
                offer,
                timeframe
            )
            events_queue.put(event)
        # Handle all penalty tasks
        sub = self.subscriptions[offer]
        sub.attribs[timeframe]['penalty'] += 1
        if sub.attribs[timeframe]['penalty'] > 5:
            # Reset
            sub.attribs[timeframe]['penalty'] = 0
            # Over 5 penalty mark as "busy" for 50 seconds
            sub.attribs[timeframe]['busy'] = True
            # Make sleeper thread
            _t = Thread(
                    target=_sleeper,
                    args=(jobno,
                          offer,
                          timeframe,
                          self.events_queue,
                          pen,)
            )
            _t.daemon = True
            _t.start()
            cprint(
                "Type: Penalty: Jobno: {0} Offer: {1} Time Frame: {2}".format(
                    jobno,
                    offer,
                    timeframe
            ), 'cyan')

    def _transact_live_data(
        self, jobno, offer, timeframe,
        sub, db_max, signal, current_bar
    ):
        """
        Handle live data response and actions
        """
        if db_max >= signal:
            # Complete
            sub.attribs[timeframe]['jobno']+=1
        else:
            # Add penalty
            self._penalty_box(jobno, offer, timeframe)
        # Check if we need to resend
        if sub.signal_valid(signal, current_bar, timeframe):
            # Create and place event into queue.
            self._create_data_event(
                jobno, offer, timeframe, db_max, current_bar)

    def _transact_historical_data(
        self, jobno, offer, timeframe,
        sub, db_max, signal, current_bar
    ):
        """
        Handle historical data response and actions.
        """
        if jobno < 0:
            sub.attribs[timeframe]['jobno']+=1
            if db_max < signal:
                # Get new jobno
                jobno = sub.attribs[timeframe]['jobno']
                # Create and place event into queue.
                self._create_data_event(
                    jobno, offer, timeframe, db_max, current_bar)
            else:
                # Set jobno to Zero.
                sub.attribs[timeframe]['jobno'] = 0

    def response(self, jobno, offer, timeframe):
        """
        Handles any historical or live ResponseEvent to the
        subscribed offer, by calling the respective
        _transact_historical_data and _transact_live_data
        methods.
        """
        sub = self.subscriptions[offer]
        # Start and end database dates
        db_min, db_max = self.db.extremity_dates(offer, timeframe)
        sub.attribs[timeframe]['db_min'] = db_min
        sub.attribs[timeframe]['db_max'] = db_max
        # Current signal
        signal = self.signals[timeframe]['fin']
        current_bar = self.signals[timeframe]['cur']
        # Remove "busy" flag from Offer.
        sub.attribs[timeframe]['busy'] = False
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

    def check_subscription(self):
        """
        This method is called on every loop in the
        CollectionSession
        
        Loop over each subscription and time frame to check
        if they are up to date.
        
        If any update requirements are found a DataEvent
        will be placed into the queue.
        """
        s = self.subscriptions
        iter_jobs = [(x,y) for x in s for y in s[x].timeframes]
        for offer, timeframe in iter_jobs:
            # Get signal and current bar date time
            signal = self.signals[timeframe]['fin']
            current_bar = self.signals[timeframe]['cur']
            # Check if the signal is valid
            if s[offer].signal_valid(signal, current_bar, timeframe):
                dtfm = s[offer].attribs[timeframe]['db_max']
                jobno = s[offer].attribs[timeframe]['jobno']
                # Create and place event into queue.
                self._create_data_event(
                    jobno, offer, timeframe, dtfm, current_bar)
            else:
                # Do nothing
                pass

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
        This method is called on every loop in the CollectionSession
        Live monitoring of:
        -------------------
            Market Status: Open or Closed
            TimeStamp: Last time offer was updated
            Bid & Ask : double, double
        
        Responds to changes when market opens and closes, by
        updating the offers opening time.
        
        Saves results to JSON file.
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
                    sub.update_broker_values(
                        new_timestamp, new_status, bid, ask
                    )
                    self.save_update(o)
