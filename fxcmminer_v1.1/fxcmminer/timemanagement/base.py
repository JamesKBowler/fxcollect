from datetime import time, datetime, timedelta
from dateutil import tz
import pytz
import pandas as pd

class DateTimeManagement(object):
    """
    This top level class will hold the attribuites of each the 
    instruments date and time information.
    """

    def _data_frequency(self, time_frame):
        freq_keys = {
            'm1' : ['1T', 'minutes', 1],
            'm5' : ['5T', 'minutes', 5],
            'm15': ['15T', 'minutes', 15],
            'm30': ['30T', 'minutes', 30],
            'H1' : ['1H', 'hours', 1],
            'H2' : ['1H', 'hours', 1],
            'H4' : ['1H', 'hours', 1],
            'H8' : ['1H', 'hours', 1],
            'D1' : ['1D', 'days', 1],
            'W1' : ['1W', 'weeks', 1]
        }
        return freq_keys[time_frame]

    def new_york_offset(self, init_date, hour):
        """
        Adjusts the time based on the US/Eastern timezone, however
        this is not a DST offset, rather an adjustment made by FXCM for
        New York opening.
        """
        newyork = pytz.timezone('US/Eastern')
        init_date = newyork.localize(init_date, is_dst=None)
        assert init_date.tzinfo is not None
        assert init_date.tzinfo.utcoffset(init_date) is not None
        isdst = bool(init_date.dst())
        if isdst:
            hour -= 1
        return hour

    def get_trading_week(self, init_date):
        """
        Creates the corrasponding forex trading week.
        Forex Opening Hours are:
        Sunday 21:00 - Friday 20:59 (UTC)
        """
        trading_week_start = init_date - timedelta(
            7+((init_date.weekday() + 1) % 7)-(7))
        trading_week_end = trading_week_start + timedelta(days=5)
        if init_date >= trading_week_end:
            trading_week_start += timedelta(days=7)
            trading_week_end += timedelta(days=7)
        fx_open_hour = self.new_york_offset(init_date, 22)
        trading_week_start = trading_week_start.replace(
            hour=fx_open_hour, minute=00)
        trading_week_end = trading_week_end.replace(
            hour=fx_open_hour, minute=59)
        return trading_week_start, trading_week_end

    def get_live_range(self, to_date, time_frame):
        freq, interval_type, delta = self._data_frequency(time_frame)
        to_date += timedelta(**{interval_type:delta})
        return to_date
