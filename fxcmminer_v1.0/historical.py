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
    def historical_prices(hist_queue, live_queue, event):
        """
        Contacts the database and retrives the latest date, then continues
        with the historical data mining to the present date
        """
        def collect_data(fxc, instrument, time_frame, fm_date):
            """
            Gets the data
            """      
            time_delta = TimeDelta().get_delta(time_frame)

            to_date = None
            fm_date, to_date = DateRange().get_date_block(
                                           time_delta, fm_date, to_date)
            log(instrument).debug("[>>] Starting Block   : %s %s %s %s" % \
                                (instrument, str(fm_date), str(to_date), time_frame))
            breakout = 0
            while True:
                breakdate = datetime.datetime.now() # - datetime.timedelta(minutes = 5)
                if to_date >= breakdate or fm_date >= breakdate:
                    breakout = 1
                    d = datetime.datetime.now()
                    to_date = d.replace(second=00, microsecond=00)

                try:
                    data = fxc.get_historical_prices(
                        str(instrument), fm_date,
                        to_date, str(time_frame)) 
                    data = [d.__getstate__()[0] for d in data]

                except (KeyError, IndexError):
                    data = []

                if data != []:
                    hist_queue.put(HistDataEvent(
                        data, instrument, time_frame))

                    log(instrument).debug("[:)] Data Collected   : %s %s %s %s" % \
                        (instrument, str(fm_date), str(to_date), time_frame))
                    fm_date, to_date = DateRange().get_date_block(
                                       time_delta, fm_date, to_date)

                else:
                    log(instrument).debug("[??] Skipping Block   : %s %s %s %s" % \
                                (instrument, str(fm_date), str(to_date), time_frame))
                    fm_date, to_date = DateRange().get_date_block(
                                       time_delta, fm_date, to_date)

                del data
                
                if breakout == 1:
                    break

        fxoffer = event.fxoffer

        while True:
            try:
                fxc = fx.ForexConnectClient(s.FX_USER, s.FX_PASS,
                                            s.FX_ENVR, s.URL
                )
                if fxc.is_connected() == True:
                    break
            except RuntimeError:
                pass

        for offer, time_frames in fxoffer.iteritems():
            for time_frame in time_frames:
                date = DatabaseManager().return_date(offer, time_frame)
                collect_data(fxc, offer, time_frame, date)
                log(offer).debug("[^^] TFrame Complete  : %s |%s|" % (offer, time_frame))

            log(offer).debug("[<>] Offer Complete   : %s |%s|" % (offer, time_frame))
        print("[^^] Hist complete : %s" % offer)
        live_queue.put(LiveReadyEvent(offer))
