import re
import MySQLdb
import forexconnect as fx
from event import HistDataEvent, LiveReadyEvent
from time_delta import TimeDelta
from log import Logger as log
from time import sleep
import settings as s
from db_manager import DatabaseManager
from dates import DateRange
import datetime

class HistoricalCollector(object):
    """
    HistoricalCollector collects historic data from FXCM. 

    """
    @staticmethod
    def historical_prices(events_queue, event):
        """
        Contacts the database and retrives the latest date, then continues
        with the historical data mining to the present date
        """
        def collect_data(fxc, instrument, time_frame, fm_date):
            """
            Gets the data
            """ 
            logfile = re.sub('[^A-Za-z0-9]+','', instrument)       
            time_delta = TimeDelta().get_delta(time_frame)

            to_date = None
            fm_date, to_date = DateRange().get_date_block(
                                           time_delta, fm_date, to_date)
            log(logfile).debug("[>>] Starting Block   : %s %s %s %s" % \
                                (instrument, str(fm_date), str(to_date), time_frame))

            if to_date <= datetime.datetime.now():
                while True:
                    breakdate = datetime.datetime.now() - datetime.timedelta(minutes = 5)
                    if to_date >= breakdate or fm_date >= breakdate:
                        break

                    try:
                        data = fxc.get_historical_prices(
                            str(instrument), fm_date,
                            to_date, str(time_frame)) 
                        data = [d.__getstate__()[0] for d in data]

                    except (KeyError, IndexError):
                        data = []

                    if data != []:
                        events_queue.put(HistDataEvent(
                            data, instrument, time_frame))

                        log(logfile).debug("[:)] Data Collected   : %s %s %s %s" % \
                            (instrument, str(fm_date), str(to_date), time_frame))
                        fm_date, to_date = DateRange().get_date_block(
                                           time_delta, fm_date, to_date)

                    else:
                        log(logfile).debug("[??] Skipping Block   : %s %s %s %s" % \
                                    (instrument, str(fm_date), str(to_date), time_frame))
                        fm_date, to_date = DateRange().get_date_block(
                                           time_delta, fm_date, to_date)

                        breakdate = datetime.datetime.now() - datetime.timedelta(minutes = 5)

                    del data

        fxoffer = event.fxoffer

        while True:
            try:
                fxc = fx.ForexConnectClient(str(s.FX_USER),
                                            str(s.FX_PASS),
                                            str(s.FX_ENVR))
                if fxc.is_connected() == True:
                    break
            except RuntimeError:
                pass

        for offer, time_frames in fxoffer.iteritems():
            filename = re.sub('[^A-Za-z0-9]+','', offer)
            for time_frame in time_frames:
                date = DatabaseManager().return_date(offer, time_frame)
                collect_data(fxc, offer, time_frame, date)
                log(filename).debug("[^^] TFrame Complete  : %s |%s|" % (offer, time_frame))

            log(filename).debug("[<>] Offer Complete   : %s |%s|" % (offer, time_frame))

        events_queue.put(LiveReadyEvent(offer)) 
