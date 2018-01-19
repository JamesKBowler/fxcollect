from instrument import InstrumentAttributes
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
        self.tracked = None
        time_frames = self.br_handler.supported_time_frames
        self._initialise_instrument(
            broker, instrument, time_frames
        )

    def _initialise_instrument(
        self, broker, instrument, time_frames
    ):
        market_status, lastupdate = self.br_handler._get_status(
                instrument)
        # Get the latest daliy bar datetime
        init_dt = self.br_handler._init_datetime(instrument)
        # Initialise instrument
        i = InstrumentAttributes(
            broker, instrument, time_frames,
            market_status, lastupdate, init_dt
        )
        for time_frame in i.time_frames:
            # Finished bar published by the broker
            i.calculate_finished_bar(time_frame)
            # Earlest & Latest datetime
            dtx = self.db_handler.return_extremity_dates(
                instrument, time_frame)
            # Store database minimum and maximum datetime information
            if not dtx: # Is a new in 
                db_min = i.attrib[time_frame]['finbar']
                db_max = datetime(1899, 12, 30, 0, 0, 0)
                i.attrib[time_frame]['db_min'] = db_min
                i.attrib[time_frame]['db_max'] = db_max
                to_date = finbar
            else:
                db_min = dtx[0]
                db_max = dtx[1]
                i.attrib[time_frame]['db_min'] = db_min
                i.attrib[time_frame]['db_max'] = db_max
                to_date = db_min - timedelta(minutes=1)
            # Set first history collection dates
            from_date = datetime(1899, 12, 30, 0, 0, 0)
            # Add instrument to python dictionary
            self.tracked = i
            # Create first collecton job.
            print(
                "INIT    : %s %s dtto: %s dbmax: %s" % (
                    instrument, time_frame, to_date, db_max)
            )
            self._data_collection(
                instrument, time_frame, from_date, to_date)
            
            print(
                "DONE    : %s %s dbmin: %s dbmax: %s" % (
                    instrument, time_frame, db_min, db_max)
            )

    def _status_monitoring(self):
        while True:
            i = self.tracked
            status = self.br_handler._get_status(i.instrument)
            market_status, lastupdate = status
            i.market_status = market_status
            i.last_update = lastupdate
            if i.market_status == 'O':
                for time_frame in i.time_frames:
                    # Find the last finished bar published by the broker
                    i.calculate_finished_bar(time_frame)
                    finbar = i.attrib[time_frame]['finbar']
                    db_max = i.attrib[time_frame]['db_max']
                    if finbar > db_max:
                        from_date = db_max + timedelta(minutes=1)
                        to_date = finbar + timedelta(minutes=1)
                        print(
                            'SIGNAL  : %s %s finbar: %s dbmax: %s' % (
                                i.instrument, time_frame,
                                finbar, db_max)
                        )
                        self._data_collection(
                            i.instrument, time_frame, from_date, to_date)

            time.sleep(1)

    def _data_collection(
        self, instrument, time_frame, dtfm, dtto
    ):
        print(
            "GET     : %s %s dtfm: %s dtto: %s" % (
                instrument, time_frame, dtfm, dtto)
        )
        data = 'foobars'
        i = self.tracked
        while len(data) > 1:
            data = self.br_handler._get_bars(
                instrument, time_frame, dtfm, dtto)
            if len(data) > 0:
                pdfm = data['date'].min().item()
                pdto = data['date'].max().item()
                dtto = pdfm - timedelta(minutes=1)
                i._update_database_datetime(
                    time_frame, pdfm, pdto)
                self.db_handler.write(
                    instrument, time_frame, data)
                print(
                    "DATA    : %s %s pdfm: %s pdto: %s" % (
                        instrument, time_frame, pdfm, pdto)
                )
                if pdfm == dtfm: break

broker, instrument = sys.argv[1], sys.argv[2]
ih = CollectionHandler(broker, instrument)._status_monitoring()
