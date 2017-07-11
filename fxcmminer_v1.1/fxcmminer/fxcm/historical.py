from timemanagement.tradinghours import DateRange
from event import HistDataEvent, LiveReadyEvent
from base import AbstractFxcmHistorical
from database.base import DatabaseManager
from operator import itemgetter

class HistoricalCollector(AbstractFxcmHistorical):
    """
    HistoricalCollector collects historic data from FXCM.
    """
    def __init__(self, hist_queue, live_queue):
        """
        """
        self.hist_queue = hist_queue
        self.live_queue = live_queue
        self.date_range = DateRange()

    def _collect_data(self, fxc, instrument, time_frame, init_date):
        """
        Iterates through the DatetimeIndex provided provided by the
        DateRange class.
        """
        maxbars = 300
        if time_frame[:1] == 'H': 
            maxbars = maxbars*int(time_frame[1:])
        dtx = self.date_range.get_trading_range(
            init_date, str(time_frame))
        latest_dbdate = DatabaseManager(
            ).latest_dbdate(instrument, time_frame)
        if latest_dbdate != None:
            dtx = dtx[dtx > latest_dbdate]
        while dtx.empty == False:
            fm_date = dtx.min()
            try:
                to_date = dtx[maxbars-1]
            except IndexError:
                to_date = dtx.max()
            data = self.get_data(
                fxc, instrument, fm_date, to_date, time_frame)
            data = data.loc[
                (data.index >= fm_date) & (data.index <= to_date)
            ]
            next_dtx = dtx[maxbars:]
            if next_dtx.empty:
                next_dtx = self.date_range.get_next_trading_range(
                    to_date, time_frame)
            dtx = next_dtx[next_dtx > to_date]
            if not data.empty:
                self.hist_queue.put(HistDataEvent(
                    data, instrument, time_frame))
            del data

    def _sort_fxoffers(self, fxoffers):
        """
        The list of fxoffers is sorted by date, so that
        any offer with latest date is processed first.
        """
        offers = []
        for instrument in fxoffers:
            init_date = self._get_init_date(instrument, 'm1')
            offers.append([instrument, init_date])
        offers = sorted(offers, key=itemgetter(1), reverse=True)
        return offers

    def _historical_iter(self, fxoffers, time_frames):
        """
        Iterates over each instrument and time frame, once all
        historical data is collected, a LiveReady event is place
        in to the queue.
        """
        fx_offers = self._sort_fxoffers(fxoffers)
        fxc = self._fx_connection()
        for ins in fx_offers:
            for time_frame in time_frames:
                instrument = ins[0]
                print("[^^] HIST  | Starting : %s %s" % (
                    instrument, time_frame))
                init_date = self._get_init_date(instrument, time_frame)
                self._collect_data(
                    fxc, instrument, time_frame, init_date)
                print("[^^] HIST  | Complete : %s %s" % (
                    instrument, time_frame))
            self.live_queue.put(LiveReadyEvent(instrument))
        fxc.logout()

    def historical_prices(self, event):
        """
        Starts the collection of historical data
        """
        self._historical_iter(event.fxoffers, event.time_frames)
