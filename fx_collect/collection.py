from instrument import InstrumentAttributes
from broker import FXCMBrokerHandler
from database import DatabaseHandler
from time_keeper import TimeKeeper
from settings import JSON_DIR
from logger import Logger

import numpy as np
import time
import json
import sys
import os


class DataCollectionHandler(object):
    def __init__(self, broker, instrument):
        """
        The purpose of 'fx_collect' is to automate the collection
        of historical and live financial time series data from
        FXCM, then store these data in a MariaDB database ready
        for back-testing or live execution.
        """
        self.broker = broker
        self.instrument = instrument
        self.br_handler = FXCMBrokerHandler()
        self.time_frames = self.br_handler.supported_time_frames
        self.db_handler = DatabaseHandler(broker)
        init_dt = self.br_handler.get_initial_datetime(instrument)
        self.time_keeper = TimeKeeper(init_dt)

        self._json_dir = os.path.join(
            JSON_DIR, "%s" % instrument.replace('/',''))
        self._ole = self.time_keeper.return_ole_zero()
        self._utc_now = self.time_keeper.utc_now()

        self._initialise_instrument()
        self._first_collection()
        self._catchup_collection()
        self._live_data_collection()

    def _initialise_instrument(self):
        """
        Setup initial instrument attributes and perform the
        a finished bar calculation.
        """
        # Initialise instrument
        self.ins = InstrumentAttributes(
                self.broker,
                self.instrument,
                self.time_frames,
                last_update=self._utc_now
        )
        for time_frame in self.time_frames:
            # Earliest & Latest date time for time_frame
            # from the database
            dtx = self.db_handler.return_extremity_dates(
                instrument, time_frame)
            if dtx:  # Dates found
                db_min, db_max = dtx
            else:  # No dates
                db_min, db_max = self._utc_now, self._ole
            # Store database min and max date time information
            self.ins.attribs[time_frame]['db_min'] = db_min
            self.ins.attribs[time_frame]['db_max'] = db_max
            # Initial finished bar calculation
            self._calculate_finished_bar(time_frame)

    def _first_collection(self):
        """
        On system startup the instrument will either start
        from the beginning or where the program was stopped
        previously.
        """
        if not os.path.exists(self._json_dir):
            # Instrument is new or not finished
            dtfm = self._ole
            for time_frame in self.time_frames:
                ins_attribs = self.ins.attribs[time_frame]
                if ins_attribs['db_max'] == self._ole:
                    # Its a new collection
                    finbar = ins_attribs['finbar']
                    dtto = self.time_keeper.add_dt(finbar)
                else:
                    # Old history needs finishing off
                    db_min = ins_attribs['db_min']
                    dtto = self.time_keeper.sub_dt(db_min)
                LOG._debug(
                    "NEW", instrument, time_frame, dtfm, dtto)
                # Create first collection job.
                self._data_collection(
                    time_frame,
                    dtfm,
                    dtto
                )

    def _catchup_collection(self):
        """
        All price data can take some time to download, this
        method ensures that all historical data is collected
        before handing off to the _live_data_collection method.

        Once history has been completed a JSON file containing
        the instrument attributes is saved.
        """
        # Instrument history is finished
        for time_frame in self.time_frames:
            self._calculate_finished_bar(time_frame)
            ins_attribs = self.ins.attribs[time_frame]
            finbar = ins_attribs['finbar']
            db_max = ins_attribs['db_max']
            dtfm = self.time_keeper.sub_dt(db_max)
            dtto = self.time_keeper.add_dt(finbar)
            if finbar > db_max:
            # Create catchup collection job.
                self._data_collection(
                    time_frame,
                    dtfm,
                    dtto
                )
            LOG._debug(
                "RDY", instrument, time_frame, dtfm, dtto)
        # Reverse time frames list so that 1 minute is processed first
        self.time_frames = self.time_frames[::-1]
        # Save initial JSON to file once historical data is complete
        self._save_update()

    def _market_condition_open(self):
        """
        The live data collection will not run if the broker
        is closed for business.
        """
        self._utc_now = self.time_keeper.utc_now()
        if self._utc_now <= self.time_keeper.stop_date():
            return True
        else:
            self.ins.market_status = 'C'
            self._save_update()
            print(
                "Stopping live collection because",
                "broker is closed for business"
            )
            return False

    def _live_data_collection(self):
        """
        On each loop the _live_data_collection method will poll the broker
        API memory for the current market status and the last update.
        This method will run indefinitely until	the broker is closed for
        business.

        When the broker has a new update, the BID and ASK are recored then
        a new finish bar calculation is performed. If the calculation
        generates a 'SIGNAL' the _data_collection method will be called,
        and finally saving those new attributes to a JSON file.
        """

        ins = self.ins

        while self._market_condition_open():
            # Retrieve instrument status from broker
            status = self.br_handler.get_offer_status(self.instrument)
            market_status, last_update = status
            if last_update > ins.last_update or market_status != ins.market_status:
                if ins.market_status == 'C':  # Stop false fires
                    # Market has just opened or program has just started
                    # get lowest minutely value for the current day
                    dt_open = self.br_handler.get_open_datetime(self.instrument)
                # Update status
                ins.last_update = last_update
                ins.market_status = market_status
                if market_status == 'O': # Open
                    bid, ask = self.br_handler.get_current_tick(self.instrument)
                    self.ins.update_instrument(
                        last_update, bid, ask
                    )
                    for time_frame in self.time_frames:
                        self._calculate_finished_bar(time_frame)
                        # Find the last finished bar published by the broker
                        finbar = ins.attribs[time_frame]['finbar']
                        db_max = ins.attribs[time_frame]['db_max']
                        if finbar > db_max and finbar > dt_open:
                            # New bar available
                            from_date = self.time_keeper.add_dt(db_max)
                            to_date = self.time_keeper.add_dt(finbar)
                            # Logging
                            LOG._debug(
                                "SIG", self.instrument, time_frame,
                                finbar, db_max)
                            # Create collection on SIGNAL.
                            self._data_collection(
                                time_frame,
                                from_date,
                                to_date
                            )
                            finbar = ins.attribs[time_frame]['finbar']
                            db_max = ins.attribs[time_frame]['db_max']
                            LOG._debug(
                                "DTA", self.instrument, time_frame,
                                finbar, db_max)
                    # Total live collection speed for all time_frames
                    speed = self._utc_now - last_update
                # Convert update to JSON and save to file
                self._save_update()
            else:
                # Broker session (memory) polling speed
                time.sleep(0.1)

    def _calculate_finished_bar(self, time_frame):
        """
        Stops unfinished bars from being written to the
        database by calculating the latest finished bar.
        """
        last_update = self.ins.last_update.replace(
            second=0,microsecond=0
        )
        fin = self.time_keeper.calculate_date(last_update, time_frame)
        # Add Finished bar
        self.ins.attribs[time_frame]['finbar'] = fin

    def _data_collection(
        self, time_frame, dtfm, dtto
    ):
        """
        All data collection methods above pass jobs through here.
        Data is first collected from the broker, then passed over
        to the DatabaseHandler for processing.
        """
        # Setup
        pdfm = dtfm
        while True:
            data = self.br_handler.get_bars(
                self.instrument, time_frame,
                dtfm, dtto
            )
            if len(data) >= 1:
                data = data[data['date'] <= dtto]
                if len(data) > 0:
                    # Get first and last date
                    pdfm = data['date'].min().item()
                    pdto = data['date'].max().item()
                else:
                    break
            else:
                break
            dtto = self.time_keeper.sub_dt(pdfm)
            self.db_handler.write(self.instrument, time_frame, data)
            self.ins.update_datetime(time_frame, pdfm, pdto)
            # Complete
            if pdfm <= dtfm:
                break

    def _save_update(self):
        """
        Saves an update to a JSON file, which can be later accessed
        from another back-testing or live-trading platform.
        """
        snapshot = self.ins.create_snapshot()
        with open(self._json_dir, 'w') as f:
            json.dump(snapshot, f)


broker, instrument = sys.argv[1], sys.argv[2]
LOG = Logger(instrument.replace('/',''))

#broker, instrument = 'fxcm', 'GBP/USD'
ih = DataCollectionHandler(broker, instrument)
