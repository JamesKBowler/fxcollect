from datetime import time, datetime, timedelta
from dateutil import tz
import pytz
import pandas as pd
from .base import DateTimeManagement

class DateRange(DateTimeManagement):
    """
    The DataRange class provide a mechanism for interacting with
    multiple time frames. If a timestamp is provided to this class
    the corasponing trading week is returned in multiples of 300.
    300 is the maxumum bars that can be called from FXCM in any
    one API call. A daterange is returned as a DatetimeIndex
    which is then iterated over.
    """
    def get_trading_range(self, init_date, time_frame):
        """
        Selects the correct methood based on time frame
        recieved.
        """
        tr_dict = {
            'D' : lambda : self._daily_range(init_date),
            'W' : lambda : self._weekly_range(init_date),
            'M' : lambda : self._monthly_range(init_date),
            'm' : lambda : self._minutely_range(init_date, time_frame),
            'H' : lambda : self._hourly_range(init_date, time_frame)
        }
        return tr_dict[time_frame[0]]()

    def get_next_trading_range(self, init_date, time_frame):
        """
        Once the DatetimeIndex has been completely covered, this
        method will turn the next trading week.
        """
        utcnow = datetime.utcnow()
        if init_date < utcnow:
            if time_frame != 'M1':
                freq, interval_type, delta = self._data_frequency(
                    time_frame)
                init_date += timedelta(**{interval_type:delta})
            else:
                if init_date.month == 12:
                    init_date = init_date.replace(
                        year=init_date.year+1, month=2, day=1)
                elif init_date.month == 11:
                    init_date = init_date.replace(
                        year=init_date.year+1, month=1, day=1)
                else:
                    init_date = init_date.replace(
                        month=init_date.month+2, day=1)
                init_date -= timedelta(days=1)
                init_date = init_date.replace(
                    hour=self.new_york_offset(init_date, 22))
            return self.get_trading_range(init_date, time_frame)
        else:
            return pd.DatetimeIndex([])

    def _minutely_range(self, init_date, time_frame):
        """
        Returns DatetimeIndex trading week in minutes.
        """
        utcnow = datetime.utcnow()
        tr_wk_str, tr_wk_end = self.get_trading_week(init_date)
        freq, interval_type, delta = self._data_frequency(time_frame)
        if tr_wk_end > utcnow:
            utcnow = utcnow.replace(second=00, microsecond=00)
            tr_wk_end = utcnow + timedelta(**{interval_type:delta})
        dtm = pd.date_range(str(tr_wk_str), str(tr_wk_end), freq=freq)
        return dtm

    def _hourly_range(self, init_date, time_frame):
        """
        Returns DatetimeIndex trading week/s in hours.
        """
        utcnow = datetime.utcnow()
        tr_wk_str, tr_wk_end = self.get_trading_week(init_date)
        if tr_wk_end > utcnow:
            tr_wk_end = utcnow.replace(
                minute=00,second=00, microsecond=00)
        freq, interval_type, delta = self._data_frequency(time_frame)
        dth = pd.date_range(str(tr_wk_str), str(tr_wk_end), freq=freq)
        while (len(dth) % (300*int(time_frame[1:])) == 0) == False:
            tr_wk_str = tr_wk_end + timedelta(**{interval_type: delta})
            if tr_wk_str < utcnow:
                tr_wk_str, tr_wk_end = self.get_trading_week(tr_wk_str)
                if tr_wk_end > utcnow:
                    tr_wk_end = utcnow.replace(
                        minute=00,second=00, microsecond=00)
                    tr_wk_end += timedelta(hours=1)
                dth = dth.append(
                    pd.date_range(str(tr_wk_str), str(tr_wk_end), freq=freq))
            else:
                break
        return dth

    def _daily_range(self, daily):
        """
        Returns DatetimeIndex for daily values.
        """
        max_bars = 299
        utcnow = datetime.utcnow()
        dtd = pd.DatetimeIndex([])
        while daily < utcnow:
            tr_wk_str, tr_wk_end = self.get_trading_week(daily)
            hour = int(str(tr_wk_str.time())[:2])
            daily += timedelta(days=1)
            daily = daily.replace(hour=hour)
            if daily >= tr_wk_end:
                daily, tr_wk_end = self.get_trading_week(daily)
            dtd = dtd.append(
                pd.date_range(str(daily), str(daily)))
        return dtd

    def _weekly_range(self, saturday):
        """
        Returns DatetimeIndex for weekly values.
        """
        max_bars = 299
        utcnow = datetime.utcnow()
        dtw = pd.DatetimeIndex([])
        while saturday < utcnow:
            hour = self.new_york_offset(saturday, 22)
            saturday = saturday.replace(hour=hour)
            dtw = dtw.append(
                pd.date_range(str(saturday), str(saturday)))
            saturday += timedelta(days=7)
        return dtw

    def _monthly_range(self, last_day_of_month):
        """
        Returns DatetimeIndex for monthly values.
        """
        ldom = last_day_of_month
        max_bars = 299
        utcnow = datetime.utcnow()
        dtm = pd.DatetimeIndex([])
        while ldom < utcnow:
            dtm = dtm.append(pd.date_range(
                str(ldom), str(ldom)))
            if ldom.month == 12:
                ldom = ldom.replace(year=ldom.year+1, month=2, day=1)
            elif ldom.month == 11:
                ldom = ldom.replace(year=ldom.year+1, month=1, day=1)
            else:
                ldom = ldom.replace(month=ldom.month+2, day=1)
            ldom -= timedelta(days=1)
            ldom = ldom.replace(hour=self.new_york_offset(ldom, 22))
        return dtm
