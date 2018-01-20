from instrument import InstrumentAttributes
from datetime import datetime, timedelta
from broker import FXCMBrokerHandler
from database import DatabaseHandler
from settings import JSON_DIR

import time
import sys
import json

LOG = Logger()

class InstrumentCollectionHandler(object):
    def __init__(self, broker, instrument):
        """
        The purpose of 'fxcmminer' is to automate the collection
        of historical and live financial time serais data from
        FXCM, then store these data in a MariaDB database ready
        for backtesting or live execution.
        """              
        self.br_handler = FXCMBrokerHandler()
        self.db_handler = DatabaseHandler('fxcm')
        self.tracked = None
        time_frames = self.br_handler.supported_time_frames
        self._initialise_instrument(
            broker, instrument, time_frames
        )
              
    def _initialise_instrument(
        self, broker, instrument, time_frames
    ):
        # Retrive instrument attribuites from broker
        status = self.br_handler._get_status(instrument)
        market_status, lastupdate = status
        # Get the latest daliy bar datetime & setup
        # instrument datetime calculation varables
        init_dt = self.br_handler._init_datetime(instrument)
        utc_now = datetime.utcnow()
        wk_str = init_dt - timedelta(days=dt.weekday()+1)
        wk_end = wk_str + timedelta(days=5, minutes=-1)
        # Live collection stop date
        self.stop_date = wk_end + timedelta(minutes=1)
        # Initialise instrument
        self.tracked = InstrumentAttributes(
                broker, instrument, time_frames,
                market_status, last_update,
                utc_now, wk_str, wk_end
        )
        self._setup_first_collection(instrument, time_frames)

    def _calculate_finished_bar(self, time_frame):
        """
        Stops unfinished bars from being written to the
        database by calculating the latest finshed bar.
        """
        lu = self.tracked.last_update.replace(
            second=0,microsecond=0
        )
        tf = int(time_frame[1:])
        # New York Offset
        if self.tracked.td % 2 == 0: nyo = 1
        else: nyo = 2
        # Select time_frame last bar calculation
        if time_frame[:1] == "m":
            # Minutely Bar
            adj = lu
            l = list(range(0,60,tf))
            cm = min(
                l, key=lambda x:abs(x-adj.minute)
            )
            fin = adj.replace(minute=cm)-timedelta(minutes=tf)

        elif time_frame[:1] == "H":
            # Hourly Bar
            adj = lu.replace(minute=0)
            l = [
                  e-nyo for e in [
             i + tf - 2 for i in list(range(1,25,tf))
                  ]
            ]
            ch = min(l, key=lambda x:abs(x-adj.hour))
            fin = adj.replace(hour=ch)-timedelta(hours=tf)

        elif time_frame[:1] == "D":
            # Daliy Bar
            adj = lu.replace(hour=self.tracked.sw_hour,minute=0)
            fin = adj - timedelta(days=tf)

        elif time_frame[:1] == "M":
            # Monthly Bar
            adj = lu.replace(day=1,hour=self.tracked.sw_hour,minute=0)
            fin = adj - timedelta(days=1)

        else:
            raise NotImplmented("Time-frame : %s Not Supported")

            # Add Finished bar
        self.tracked.attrib[time_frame]['finbar'] = fin
        
    def _setup_first_collection(
        self, instrument, time_frames
    ):
        for time_frame in time_frames:
            # Inital finished bar calculation
            self._calculate_finished_bar(time_frame)
            # Earlest & Latest datetime for time_frame
            dtx = self.db_handler.return_extremity_dates(
                instrument, time_frame)
            # Set first history collection dates
            from_date = datetime(1899, 12, 30, 0, 0, 0)  # OLE_ZERO
            if dtx:  # Start from lowest db date
                db_min, db_max = dtx
                to_date = db_min - timedelta(minutes=1)
            else: # No dates, starting new
                db_min, db_max = utc_now, from_date
                to_date = self.tracked.attrib[time_frame]['finbar']
            # Store database min and max datetime information
            self.tracked.attrib[time_frame]['db_min'] = db_min
            self.tracked.attrib[time_frame]['db_max'] = db_max
            # Logging
            LOG.debug("INIT", instrument, time_frame,
                              market_status, to_date, db_max)
            # Create first collecton job.  
            self._data_collection(
                instrument, time_frame, from_date, to_date)

        # Save JSON to file
        self._save_update()

    def _data_collection(
        self, instrument, time_frame, dtfm, dtto
    ):
        # Logging
        LOG.debug("GET", instrument, time_frame,
            market_status, dtfm, dtto)
        # Setup
        data = 'foobars'
        init_dtto = dtto
        while len(data) > 1: 
            data = self.br_handler._get_bars(
                instrument, time_frame, dtfm, dtto)
            if len(data) > 0:
                # Get first and last date
                pdfm = data['date'].min().item()
                pdto = data['date'].max().item()
                # Avoiding time overlap
                dtto = pdfm - timedelta(minutes=1)
                # Update database
                self.db_handler.write(
                    instrument, time_frame, data)
                # Update instrument attribuites
                self.tracked.update_database_datetime(
                    time_frame, pdfm, pdto
                )
                if pdfm == dtfm: break  # Complete
        # Logging
        LOG.debug("DATA", instrument, time_frame,
            market_status, dtfm, init_dtto)

    def _market_condition_open(self):
        self.utc_now = datetime.utcnow()
        if self.utc_now <= self.stop_date:
            return True
        else:
            self.tracked.market_status = 'C'
            self._save_update()
            print(
                "Stopping live collection because broker is",
                "now closed for bussiness"
            )
            return False

    def status_monitoring(self):
        prev_update = datetime(1899, 12, 30)
        prev_status = 'C'
        while self._market_condition_open():
            # Retrive instrument attribuites from broker
            # and get current utc datetime
            instrument = self.tracked.instrument
            status = self.br_handler._get_status(instrument)
            market_status, lastupdate = status
            if lastupdate > prev_update or prev_status != market_status:
                bid, ask = self.br_handler._get_next_tick(instrument)
                self.tracked.update_instrument_status(
                    lastupdate, market_status,  
                    self.utc_now, bid, ask
                )
                prev_update = lastupdate
                prev_status = market_status
                if market_status == 'O': # Open
                    for time_frame in self.tracked.time_frames:
                        # Find the last finished bar published by the broker
                        self.calculate_finished_bar(time_frame)
                        finbar = self.tracked.attrib[time_frame]['finbar']
                        db_max = self.tracked.attrib[time_frame]['db_max']
                        if finbar > db_max:
                            # New bar available
                            from_date = db_max + timedelta(minutes=1)
                            to_date = finbar + timedelta(minutes=1)
                            # Logging
                            LOG.debug("SIGNAL", instrument, time_frame,
                                market_status, finbar, db_max)
                            # Create collecton on SIGNAL.
                            self._data_collection(
                                instrument, time_frame, from_date, to_date)
                    # Total live collection speed for all time_frames
                    speed = datetime.utc_now() - lastupdate
                # Save JSON to file
                self._save_update()
            # Broker polling speed
            time.sleep(0.1)

    def _save_update(self):
        snapshot = self.tracked.create_snapshot()
        JSON_DIR += self.tracked.instrument.replace('/','')
        with open(JSON_DIR, 'w') as f:
            json.dump(snapshot, f)

broker, instrument = sys.argv[1], sys.argv[2]
ih = InstrumentCollectionHandler(broker, instrument).status_monitoring()
