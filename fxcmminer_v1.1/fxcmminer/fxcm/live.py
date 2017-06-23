from timemanagement.tradinghours import DateRange
from event import LiveDataEvent
from base import AbstractFxcmLive
from database.base import DatabaseManager
from timemanagement.base import DateTimeManagement


class LiveCollector(AbstractFxcmLive):
    """
    Creates time based event for collecting FXCM data.
    
    Information on this API
    https://apscheduler.readthedocs.io/en/latest/
    https://github.com/agronholm/apscheduler/
    """
    def __init__(self, live_queue):
        """
        """
        self.live_queue = live_queue
        self.date_range = DateRange()
        self.get_live_range = DateTimeManagement().get_live_range

    def _collect_data(self, fxc, instrument, time_frame, last_dbdate):
        """
        Iterates through the DatetimeIndex provided provided by the
        DateRange class.
        """
        dtx = self.date_range.get_trading_range(
            last_dbdate, str(time_frame))
        dtx = dtx[dtx > last_dbdate]
        if not dtx.empty:
            fm_date = dtx.min()
            to_date = dtx.max() 
            if time_frame != 'M1':
                to_date = self.get_live_range(to_date, time_frame)
            #print('[>>] LIVE  | Collect  : %s %s %s %s' % (
            #    fm_date, to_date, instrument, time_frame))
            data = self.get_data(
                fxc, instrument, fm_date, to_date, time_frame)
            data = data[data.index > last_dbdate]
            if not data.empty:
                self.live_queue.put(LiveDataEvent(
                    data, instrument, time_frame))
            del data

    def _live_iter(self, instruments, time_frame):
        """
        Iterates over instruments list.
        """
        fxc = self._fx_connection()
        for instrument in instruments:
            last_dbdate = self._get_init_date(instrument, time_frame)
            self._collect_data(fxc, instrument, time_frame, last_dbdate)
        fxc.logout()

    def live_prices(self, offer, time_frame):
        """
        Contacts the database and retrives the latest date, then continues
        with the live data mining to the present date
        """
        self._live_iter(offer, time_frame)
