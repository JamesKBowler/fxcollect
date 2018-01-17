from instrument import Instrument
from datetime import datetime, timedelta
from broker import FXCMBrokerHandler
from database import DatabaseHandler

import time
import sys


class CollectionHandler(object):
    def __init__(
        self, broker, instrument
    ):
        self.br_handler = FXCMBrokerHandler()
        self.db_handler = DatabaseHandler('fxcm')
        self.time_frames = self.br_handler.supported_time_frames
        self.tracked = {}
        for time_frame in self.time_frames:
            self._initialise_instrument(
                broker, instrument, time_frame
            )

    def _initialise_instrument(
        self, broker, instrument, time_frame
    ):
        market_status, lastupdate = self.br_handler._get_status(
                instrument)
        # Get the latest daliy bar datetime
        init_dt = self.br_handler._init_datetime(instrument)
        # Initialise instrument
        i = Instrument(
            broker, instrument, time_frame,
            market_status, lastupdate, init_dt
        )
        # Finished bar published by the broker
        i.calculate_finished_bar()
        # Earlest & Latest datetime
        xtrdates = self.db_handler.return_extremity_dates(
            instrument, time_frame)
        # Store database minimum and maximum datetime information
        if not xtrdates: # Is new instrument 
            i.db_min = i.fin_bar
            i.db_max = datetime(1899, 12, 30, 0, 0, 0)
        else: 
            i.db_min = xtrdates[0] - timedelta(minutes=1)
            i.db_max = xtrdates[1]
        # Set first job history collection dates
        from_date = datetime(1899, 12, 30, 0, 0, 0)
        to_date = i.db_min
        # Add instrument to python dictionary
        self.instrument = i
        self.tracked[time_frame] = i
        # Create first collecton job.
        self._data_collection(
            instrument, time_frame, from_date, to_date)
        print(
            "Data Stored       : %s %s %s %s" % (
                instrument, time_frame, i.db_min, i.db_max)
        )

    def _data_collection(
        self, instrument, time_frame, dtfm, dtto
    ):
        data = 'foobars'
        i = self.tracked[time_frame]
        while len(data) > 1:
            data = self.br_handler._get_bars(
                instrument, time_frame, dtfm, dtto)
            if len(data) > 0:
                pd_min = data['date'].min().item()
                pd_max = data['date'].max().item()
                dtto = pd_min - timedelta(minutes=1)
                if pd_min < i.db_min: i.db_min = pd_min
                if pd_max >= i.db_max: i.db_max = pd_max
                self.db_handler.write(
                    instrument, time_frame, data)
                if pd_min == dtfm: break

    def _status_monitoring(self):
        while True:
            market_status, lastupdate = self.br_handler._get_status(
                i.instrument)
            for tf in self.tracked:
                i = self.tracked[tf]
                i.update(lastupdate, market_status)
                i.market_status = 'Open'
                if i.market_status == 'Open':
                    # Find the last finished bar published by the broker
                    i.calculate_finished_bar()
                    if i.fin_bar > i.db_max:
                        from_date = i.db_max + timedelta(minutes=1)
                        to_date = i.fin_bar + timedelta(minutes=1)
                        print(
                            "Status Collection : %s %s %s %s" % (
                                i.instrument, i.time_frame, from_date, to_date)
                        )
                        self._data_collection(
                            i.instrument, i.time_frame, from_date, to_date)
            time.sleep(1)

broker, instrument = sys.argv[1], sys.argv[2]
ch = CollectionHandler(broker, instrument)._status_monitoring()
