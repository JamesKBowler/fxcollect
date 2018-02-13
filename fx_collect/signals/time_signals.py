from ..event import SignalEvent
from datetime import datetime, timedelta
import numpy as np
import pytz

class TimeSignals(object):
    def __init__(self, events_queue, time_frames, start_date, end_date):
        print("Week Start: {0} End: {1}".format(start_date, end_date))
        self.events_queue = events_queue
        self._time_frames = time_frames
        self._deltas = [1,5,15,30,60,120,240,480,1440,0,0]
        self.cur_time = datetime.utcnow()
        self.start_date = start_date
        self.end_date = end_date
        self.signals = self._merge_all_signals()
        self.init_signals = self.get_init_signals()

    def _merge_all_signals(self):
        base = np.arange(
            self.start_date, self.end_date, dtype='datetime64[m]'
        )
        arr_list = []
        for d, tf in zip(self._deltas, self._time_frames):
            if tf == 'M1':
                merged = self._find_monthly_signal()
            elif tf == 'W1':    
                merged = self._find_weekly_signal()
            else:
                merged = self._find_else_signal(base, d, tf)
            arr_list.append(merged)
            
        _a =  np.array(
            sorted(np.concatenate(arr_list), key=lambda x: x[0])
        )
        # Fix start and end signals
        fs, fe = [], []        
        for s in _a[_a[:,0] == self.start_date]:
            fs.append([s[0],s[1]-timedelta(days=2),s[2],s[3]])
        for e in _a[_a[:,2] == self.end_date]:
            fe.append([e[0],e[1],e[2]+timedelta(days=2),e[3]])
        # Remove the wrong start and end signals
        a = _a[_a[:,0] != self.start_date]
        arr1 = a[a[:,2] != self.end_date]
        arr2 = np.array(fs)
        arr3 = np.array(fe)
        # Merge and sort all signals by date
        return np.array(sorted(np.concatenate(
            [arr1, arr2, arr3]), key=lambda x: x[0]))

    def get_init_signals(self):
        init_signals = {}
        for tf in self._time_frames:
            s = self.signals[self.signals[:,3] == tf][0]
            init_signals[tf] = {
                'fin':s[0], 'cur':s[1], 'nxt':s[2]
            }
        return init_signals

    def _ny(self, dt):
        """
        Adjusts the time based on the US/Eastern timezone,
        for New York opening.
        """
        offset = 0
        newyork = pytz.timezone('US/Eastern')
        nydt = newyork.localize(dt, is_dst=None)
        assert nydt.tzinfo is not None
        assert nydt.tzinfo.utcoffset(nydt) is not None
        isdst = bool(nydt.dst())
        if isdst:
            offset = 1
        return dt - timedelta(hours=offset)

    def _find_monthly_signal(self):
        def end_of_next_month(dt):
            month = dt.month + 2
            year = dt.year
            if month >= 11:
                if month == 11:
                    month = 1
                if month == 12:
                    month = 2
                year+=1
            return (
                dt.replace(
                    year=year, month=month, day=1
                ) - timedelta(days=1)
            )
        def end_of_month(dt):
            month = dt.month + 1
            year = dt.year
            if month == 12:
                month = 1
                year+=1
            return (
                dt.replace(
                    year=year, month=month, day=1
                ) - timedelta(days=1)
            )
        def end_of_last_month(dt):
            return dt.replace(day=1) - timedelta(days=1)

        init_month = end_of_month(self.start_date)
        if self.cur_time >= init_month:
            curr = init_month
        else:
            curr = end_of_last_month(init_month)
        M_curr = np.array([curr])
        M_sig = np.array([self._ny(end_of_next_month(curr))])
        M_fin = np.array([end_of_last_month(curr)])
        chars = np.empty(M_sig.size, dtype='<U3')
        chars[:] = 'M1'
        arr = np.array([M_curr, M_fin, M_sig, chars])
        return np.column_stack(arr)
        
    def _find_weekly_signal(self):
        curr = self.start_date - timedelta(days=1)
        W_curr = np.array([curr])
        W_fin = np.array([curr - timedelta(days=7)])
        W_sig = np.array([self._ny(curr + timedelta(days=8))])
        chars = np.empty(W_sig.size, dtype='<U3')
        chars[:] = 'W1'
        arr = np.array([W_curr, W_fin, W_sig, chars])
        return np.column_stack(arr) 
    
    def _find_else_signal(self, base, d, tf):
        sig = base[0::d]
        fin = base[0::d] - d
        nxt = base[0::d] + d
        chars = np.empty(sig.size, dtype='<U3')
        chars[:] = tf
        s = np.row_stack(sig)
        f = np.row_stack(fin)
        n = np.row_stack(nxt)
        c = np.row_stack(chars)
        arr = np.array([s,f,n,c])
        return np.column_stack(arr)

    def _place_signal_into_queue(self, s):
        signal_event = SignalEvent(
            finished_bar=s[1],
            current_bar=s[0],
            next_bar=s[2],
            timeframe=s[3]
        )
        self.events_queue.put(signal_event)
        
    def generate_signals(self):
        self.cur_time = datetime.utcnow()
        signals_found = self.signals[self.signals[:,0] <= self.cur_time]
        self.signals = self.signals[self.signals[:,0] > self.cur_time]
        for signal in signals_found:
            self._place_signal_into_queue(signal)
