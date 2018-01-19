from instrument import Instrument
from datetime import datetime, timedelta
from broker import FXCMBrokerHandler
from database import DatabaseHandler

import time
import sys


class CollectionHandler(object):
    def __init__(self, broker, instrument):
        """
        The purpose of 'fxcmminer' is to automate the collection
        of historical and live financial time serais data from
        FXCM, then store these data in a MariaDB database ready
        for backtesting or live execution.
        """
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
        if not xtrdates: # Is a new in 
            i.db_min = i.fin_bar
            i.db_max = datetime(1899, 12, 30, 0, 0, 0)
        else:
            i.db_min = xtrdates[0] - timedelta(minutes=1)
            i.db_max = xtrdates[1]
        # Set first history collection dates
        from_date = datetime(1899, 12, 30, 0, 0, 0)
        to_date = i.db_min
        # Add instrument to python dictionary
        self.instrument = i
        self.tracked[time_frame] = i
        # Create first collecton job.
        print(
            "INIT    : %s %s dbmin: %s dbmax: %s" % (
                instrument, time_frame, i.db_min, i.db_max)
        )
        self._data_collection(
            instrument, time_frame, from_date, to_date)
        print(
            "DONE    : %s %s dbmin: %s dbmax: %s" % (
                instrument, time_frame, i.db_min, i.db_max)
        )

    def _status_monitoring(self):
        while True:
            update = self.br_handler._get_status()
            for tf in self.tracked:
                i = self.tracked[tf]
                market_status = update[i.instrument][0]
                lastupdate = update[i.instrument][1]
                i.update(lastupdate, market_status)
                if i.market_status == 'O':  # Open
                    # Find the last finished bar published by the broker
                    i.calculate_finished_bar()
                    if i.fin_bar > i.db_max:
                        print(
                            'SIGNAL  : %s %s finbar: %s dbmax: %s' % (
                                i.instrument, i.time_frame, i.fin_bar,i.db_max)
                        )
                        from_date = i.db_max + timedelta(minutes=1)
                        to_date = i.fin_bar + timedelta(minutes=1)
                        self._data_collection(
                            i.instrument, i.time_frame, from_date, to_date)
            time.sleep(1)

    def _data_collection(
        self, instrument, time_frame, dtfm, dtto
    ):
        print(
            "GET     : %s %s dtfm: %s dtto: %s" % (
                instrument, time_frame, dtfm, dtto)
        )
        data = 'foobars'
        i = self.tracked[time_frame]
        while len(data) > 1:
            data = self.br_handler._get_bars(
                instrument, time_frame, dtfm, dtto)
            if len(data) > 0:
                pdfm = data['date'].min().item()
                pdto = data['date'].max().item()
                dtto = pdfm - timedelta(minutes=1)
                if pdfm < i.db_min: i.db_min = pdfm
                if pdto >= i.db_max: i.db_max = pdto
                self.db_handler.write(
                    instrument, time_frame, data)
                print(
                    "DATA    : %s %s pdfm: %s pdto: %s" % (
                        i.instrument, i.time_frame, pdfm, pdto)
                )
                if pdfm == dtfm: break

broker, instrument = sys.argv[1], sys.argv[2]
ih = CollectionHandler(broker, instrument)._status_monitoring()
