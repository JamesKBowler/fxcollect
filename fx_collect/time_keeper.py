from datetime import datetime, timedelta
import numpy as np
import pytz

class TimeKeeper(object):
    """
    The TimeKeeper class controls all date time logic.
    """
    def __init__(self, init_dt):
        # init_dt is the current daily bar
        # init_dt = datetime(2018,1,29,22,0) 
        self._create_current_tradingweek(init_dt)
        self._create_datetime_ranges()
   
    def _create_current_tradingweek(self, init_dt):
        """Takes the latest daily bar date time to setup
        initial system dates."""
        if init_dt.weekday() == 6: # Its Sunday
            self.wk_str = init_dt
        else:
            self.wk_str = init_dt - timedelta(days=init_dt.weekday()+1)
        self.wk_end = self.wk_str + timedelta(days=5)

    def _create_datetime_ranges(self):
        """Time frame date time ranges"""
        self.minutely_rng = self._minutely_rng()
        self.hourly_rng = self._hourly_rng()
        self.daily_rng = self._daily_rng()
        self.weekly_rng = self._weekly_rng()
        self.monthly_rng = self._monthly_rng()

    def _calc(self, lu, rng):
        """ All other time frame calculations"""
        try:
            x = rng[rng > lu][0]
            index = np.where(rng==x)[0].item()
            if index-2 < 0:
                x = rng[-1].item()
                fin = x - timedelta(days=7)
            else:
                fin = rng[index-2].item()
        except IndexError:
            index = np.where(rng==rng[-1])[0].item()
            fin = rng[index-1].item()
        return fin

    def _mcalc(self, lu):
        """Perform monthly calculation"""
        rng = self.monthly_rng
        try:
            x = rng[rng > lu][0]
            index = np.where(rng==x)[0].item()
            if index-2 < 0:
                x = rng[index-2].item()
                fin = x.replace(year=x.year-1)
            else:
                fin = rng[index-2].item()
        except IndexError:
            index = np.where(rng==rng[-1])[0].item()
            fin = rng[index-1].item()
        return fin

    def _minutely_rng(self):
        """Returns minutely numpy array"""
        return np.arange(
            self.wk_str, self.wk_end, dtype='datetime64[m]'
        )

    def _hourly_rng(self):
        """Returns hourly numpy array"""
        return np.arange(
            self.wk_str, self.wk_end, dtype='datetime64[h]'
        )

    def _daily_rng(self):
        """Returns daily numpy array"""
        d = np.arange(
            self.wk_str, self.wk_end, dtype='datetime64[D]'
        )
        return d + np.timedelta64(22, 'h')

    def _weekly_rng(self):
        """Returns all Saturdays weekly numpy array"""
        str_sat = self.wk_str.replace(month=1,day=1)
        str_sat += timedelta(days=5-str_sat.weekday())
        end_sat = str_sat + timedelta(weeks=52)
        w = np.arange(str_sat, end_sat, dtype='datetime64[D]')
        return self._ny((w + np.timedelta64(22, 'h'))[0::7])

    def _monthly_rng(self):
        """Returns all end of month numpy array"""
        m = np.arange(
            self.wk_str.replace(day=1,month=1),
            self.wk_str+timedelta(weeks=52),
            dtype='datetime64[M]'
        ) + np.timedelta64(1,'M')
        end_of_month = m - np.timedelta64(1,'D')
        return self._ny(end_of_month + np.timedelta64(22, 'h'))

    def _ny(self, np_arr):
        """
        Adjusts the time based on the US/Eastern timezone,
        for New York opening.
        """
        l = []
        offset = 0
        for i in np_arr:
            dt = i.item()
            newyork = pytz.timezone('US/Eastern')
            nydt = newyork.localize(dt, is_dst=None)
            assert nydt.tzinfo is not None
            assert nydt.tzinfo.utcoffset(nydt) is not None
            isdst = bool(nydt.dst())
            if isdst:
                offset = 1
            l.append(i - offset)
        return np.array(l)
    
    def stop_date(self):
        """Returns the system stop time"""
        return self.wk_end + timedelta(minutes=1)
    
    def utc_now(self):
        """Returns the current time in UTC"""
        return datetime.utcnow()
    
    def return_ole_zero(self):
        return datetime(1899, 12, 30)  # OLE_ZERO
    
    def sub_dt(self, dt):
        return dt - timedelta(minutes=1)
      
    def add_dt(self, dt):
        return dt + timedelta(minutes=1)
    
    def calculate_date(self, last_update, time_frame):
        """Calculation selector """
        lu = last_update.replace(second=0,microsecond=0)
        tf = time_frame[:1]
        delta = int(time_frame[1:])
        if tf == 'm':  # minutely
            rng = self.minutely_rng[0::delta]
        elif tf == 'H':  # houly
            rng = self.hourly_rng[0::delta]
        elif tf == 'D':  # daily
            rng = self.daily_rng
        elif tf == 'W':  # weekly
            rng = self.weekly_rng
        elif tf == 'W':  # weekly
            rng = self.weekly_rng
        if tf is not 'M': 
            # All other time frames
            return self._calc(lu, rng)
        else:
            # Monthly
            return self._mcalc(lu)
