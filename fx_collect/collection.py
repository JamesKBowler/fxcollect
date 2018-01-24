from instrument import InstrumentAttributes
from broker import FXCMBrokerHandler
from database import DatabaseHandler
from settings import JSON_DIR
from logger import Logger

from datetime import datetime, timedelta

import numpy as np
import time
import json
import sys
import os


class InstrumentCollectionHandler(object):
    def __init__(self, broker, instrument):
        """
        The purpose of 'fxcollect' is to automate the collection
        of historical and live financial time series data from
        FXCM, then store these data in a MariaDB database ready
        for backtesting or live execution.
        """              
        self.br_handler = FXCMBrokerHandler()
        self.db_handler = DatabaseHandler(broker)
        self.tracked = None
        time_frames = self.br_handler.supported_time_frames
        self._initialise_datetime(instrument)
        self._initialise_instrument(
            broker, instrument, time_frames
        )

    def _initialise_datetime(
        self, instrument
    ):
        # Get the latest daliy bar datetime & setup
        # initial system dates.
        self.utc_now = datetime.utcnow()
        init_dt = self.br_handler.get_initial_datetime(instrument)
        if init_dt.weekday() == 6: # Its Sunday
            self.wk_str = init_dt
        else:
            self.wk_str = init_dt - timedelta(days=init_dt.weekday()+1)
        self.wk_end = self.wk_str + timedelta(days=5)        
        self.live_collection_range = np.arange(
            self.wk_str, self.wk_end, dtype='datetime64[h]')
        print(self.live_collection_range)

    def _initialise_instrument(
        self, broker, instrument, time_frames
    ):
        # Retrive instrument attribuites from broker
        status = self.br_handler.get_offer_status(instrument)
        market_status, last_update = status
        self.stop_date = self.wk_end + timedelta(minutes=1)
        # Initialise instrument
        self.instrument = instrument
        self.tracked = InstrumentAttributes(
                broker, instrument, time_frames,
                market_status, last_update,
                self.utc_now, self.wk_str, self.wk_end
        )
        self._setup_first_collection(
            instrument, time_frames, market_status
        )

    def _setup_first_collection(
        self, instrument, time_frames, market_status
    ):
        for time_frame in time_frames:
            # Inital finished bar calculation
            self._calculate_finished_bar(time_frame)
            # Earlest & Latest datetime for time_frame
            # from the database
            dtx = self.db_handler.return_extremity_dates(
                instrument, time_frame)
            # Set first history collection dates
            from_date = datetime(1899, 12, 30)  # OLE_ZERO
            if dtx:  # Start from lowest db date
                db_min, db_max = dtx
                to_date = db_min - timedelta(minutes=1)
                # Logging Current
                LOG._debug("CUR_", instrument, time_frame,
                                  market_status, db_min, db_max)
            else:  # No dates, starting new
                db_min, db_max = self.utc_now, from_date
                to_date = self.tracked.attribs[time_frame]['finbar']
                # Logging New
                LOG._debug("NEW_", instrument, time_frame,
                                  market_status, from_date, to_date)
            # Store database min and max datetime information
            self.tracked.attribs[time_frame]['db_min'] = db_min
            self.tracked.attribs[time_frame]['db_max'] = db_max
            # No point trying to collect more history from the
            # lowest datebase date if the json file has been created.
            if not os.path.exists('json_files/%s' % instrument): 
                # Create first collecton job.
                self._data_collection(
                    instrument, time_frame,
                    from_date, to_date, market_status
                )
        # Once all historical data is collected one
        # final history collection will commence before
        # proceeding with the live collection
        for time_frame in time_frames:
            # Finished bar calculation
            self._calculate_finished_bar(time_frame)
            db_min = self.tracked.attribs[time_frame]['db_min']
            db_max = self.tracked.attribs[time_frame]['db_max']
            finbar = self.tracked.attribs[time_frame]['finbar']
            # Catch up from the lastest datebase date.
            from_date = db_max + timedelta(minutes=1)
            to_date = finbar + timedelta(minutes=1)
            if db_max < finbar:
                self._data_collection(
                    instrument, time_frame,
                    from_date, to_date, market_status
                )
            # Logging 'LIVE' ready
            db_max = self.tracked.attribs[time_frame]['db_max']
            LOG._debug("RDY_", instrument, time_frame,
                              market_status, db_min, db_max)
        # Reverse time frames list so that 1 minute is processed first
        self.tracked.time_frames = self.tracked.time_frames[::-1]
        # Save initial JSON to file once historical data is complete
        self._save_update()

    def _calculate_finished_bar(self, time_frame):
        """
        Stops unfinished bars from being written to the
        database by calculating the latest finshed bar.
        """
        lu = self.tracked.last_update.replace(
            second=0,microsecond=0
        )
        tf = int(time_frame[1:])
        rng = self.live_collection_range
        # Select time_frame last bar calculation        
        if time_frame[:1] == "m":
            # Minutely Bar
            if lu > self.stop_date:
                lu = self.stop_date
            offset = lu.time().minute % tf
            unfin_time = lu - timedelta(minutes=offset)
            fin = unfin_time - timedelta(minutes=tf)
                
        elif time_frame[:1] == "H":
            # Daliy Bar
            hr_points = rng[0::tf]
            if lu < hr_points[-2]:
                next_bar = min(i for i in hr_points if i > lu)
                curr_bar = next_bar - tf
                npfin = curr_bar - tf
                if npfin < hr_points[0]: 
                    npfin = hr_points[-1] - 7*24
                fin = npfin.item()
            else:
                fin = dy_points[-1].item()

        elif time_frame[:1] == "D":
            # Daliy Bar
            dy_points = rng[0::24*tf]
            if lu < dy_points[-2]:
                next_bar = min(i for i in dy_points if i > lu)
                curr_bar = next_bar - 24*tf
                npfin = curr_bar - 24*tf
                if npfin < dy_points[0]: 
                    npfin = dy_points[-1] - 7*24
                fin = npfin.item()
            else:
                fin = dy_points[-1].item()
                
        elif time_frame[:1] == "W":
            # Weekly Bar
            curr_bar = rng[0] - 24
            fin = (curr_bar - 7*24).item()
            
        elif time_frame[:1] == "M":
            # Monthly Bar
            hour = rng[0].item().time().hour
            d = lu.replace(
                day=1,hour=hour, minute=0, second=0)
            curr_bar = d - timedelta(days=1)
            fin = curr_bar.replace(day=1) - timedelta(days=1)
        else:
            raise NotImplmented(
                "Unsupported time_frame : %s" % (time_frame)
            )
        # Add Finished bar
        self.tracked.attribs[time_frame]['finbar'] = fin

    def _data_collection(
        self, instrument, time_frame,
        dtfm, dtto, market_status
    ):
        # Logging
        LOG._debug("GET_", instrument, time_frame,
            market_status, dtfm, dtto)
        # Setup
        pdfm = dtfm
        log = False            
        while True:
            data = self.br_handler.get_bars(
                instrument, time_frame,
                dtfm, dtto
            )
            if len(data) >= 1:                    
                data = data[data['date'] <= dtto]
                if len(data) > 0:
                    # Get first and last date
                    pdfm = data['date'].min().item()
                    pdto = data['date'].max().item()
                    LOG._debug("DATA", instrument, time_frame,
                        market_status, pdfm, pdto)
                    # Avoiding time overlap
                    dtto = pdfm - timedelta(minutes=1)
                    # Update database
                    self.db_handler.write(
                        instrument, time_frame, data)
                    # Update instrument attribuites
                    self.tracked.update_database_datetime(
                        time_frame, pdfm, pdto
                    )
                    # Capture first pdto
                    if not log:
                        log_max = pdto
                        log = True
                    # Complete
                    if pdfm <= dtfm:
                        break
                else:
                    break
            else:
                break
        # Logging
        if log:
            if dtfm < pdfm: dtfm = pdfm
            LOG._debug("DONE", instrument, time_frame,
                market_status, pdfm, log_max)

    def _market_condition_open(self):
        self.utc_now = datetime.utcnow()
        if self.utc_now <= self.stop_date:
            return True
        else:
            self.tracked.market_status = 'C'
            self._save_update()
            print(
                "Stopping live collection because",
                "broker is closed for bussiness"
            )
            return False

    def status_monitoring(self):
        prev_update = datetime(1899, 12, 30)
        prev_status = 'C'
        while self._market_condition_open():
            # Retrive instrument attribuites from broker
            # and get current utc datetime
            instrument = self.tracked.instrument
            status = self.br_handler.get_offer_status(instrument)
            market_status, last_update = status
            if last_update > prev_update or prev_status != market_status:
                if prev_status == 'C':  # Stop false fires
                    # Market has just opened or program has just started
                    start_datetime = datetime.utcnow()
                bid, ask = self.br_handler.get_current_tick(instrument)
                self.tracked.update_instrument_status(
                    last_update, market_status,
                    self.utc_now, bid, ask
                )                
                prev_update = last_update
                prev_status = market_status
                if market_status == 'O': # Open
                    for time_frame in self.tracked.time_frames:
                        # Find the last finished bar published by the broker
                        self._calculate_finished_bar(time_frame)
                        finbar = self.tracked.attribs[time_frame]['finbar']
                        db_max = self.tracked.attribs[time_frame]['db_max']
                        if finbar > db_max and finbar > start_datetime:
                            # New bar available
                            from_date = db_max + timedelta(minutes=1)
                            to_date = finbar + timedelta(minutes=1)
                            # Logging
                            LOG._debug("SIG_", instrument, time_frame,
                                market_status, finbar, db_max)
                            # Create collecton on SIGNAL.
                            self._data_collection(
                                instrument, time_frame,
                                from_date, to_date, market_status
                            )
                    # Total live collection speed for all time_frames
                    speed = datetime.utcnow() - last_update
                # Convert update to JSON and save to file
                self._save_update()
            else:
                # Broker session (memory) polling speed
                time.sleep(0.1)

    def _save_update(self):
        snapshot = self.tracked.create_snapshot()
        file_dir = JSON_DIR + self.tracked.instrument.replace('/','')
        with open(file_dir, 'w') as f:
            json.dump(snapshot, f)

broker, instrument = sys.argv[1], sys.argv[2]
LOG = Logger(instrument.replace('/',''))

#broker, instrument = 'fxcm', 'GBP/USD'
ih = InstrumentCollectionHandler(broker, instrument)
ih.status_monitoring()
