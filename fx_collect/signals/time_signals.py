# The MIT License (MIT)
#
# Copyright (c) 2017 James K Bowler, Data Centauri Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import datetime, timedelta
from ..event import SignalEvent
from ..utils.date_utils import (
    end_of_last_month,
    end_of_month,
    end_of_next_month,
    new_york_offset
)
import numpy as np


class TimeSignals(object):
    """
    The TimeSignals class will generate an Array of signals for
    each time frame and place into the events queue.
    """
    def __init__(self, events_queue, start_date, end_date):
        self.events_queue = events_queue
        self._time_frames = {
            'm1': 1, 'm5': 5, 'm15': 15, 'm30': 30,
            'H1': 60, 'H2': 120, 'H4': 240, 'H8': 480,
            'D1': 1440, 'W1': None , 'M1': None
        }
        self.cur_time = datetime.utcnow()
        self.start_date = start_date
        self.end_date = end_date
        self.signals = self._merge_all_signals()
        self.init_signals = self.get_init_signals()

    def _merge_all_signals(self):
        """ 
        Encapsulate all signal creation methods and concatenate
        in a date sorted Numpy Array.
        """
        base = np.arange(
            self.start_date, self.end_date, dtype='datetime64[m]'
        )
        arr_list = []
        for tf, d in self._time_frames.items():
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
        """ Extract the first signal for each time frame """
        init_signals = {}
        for tf in self._time_frames:
            s = self.signals[self.signals[:,3] == tf][0]
            init_signals[tf] = {
                'fin':s[0], 'cur':s[1], 'nxt':s[2]
            }
        return init_signals

    def _find_monthly_signal(self):
        """ Monthly signal """
        init_month = end_of_month(self.start_date)
        if self.cur_time >= init_month:
            curr = init_month
        else:
            curr = end_of_last_month(init_month)
        M_curr = np.array([curr])
        M_sig = np.array([new_york_offset(end_of_next_month(curr))])
        M_fin = np.array([end_of_last_month(curr)])
        chars = np.empty(M_sig.size, dtype='<U3')
        chars[:] = 'M1'
        arr = np.array([M_curr, M_fin, M_sig, chars])
        return np.column_stack(arr)
        
    def _find_weekly_signal(self):
        """ Weekly signal """
        curr = self.start_date - timedelta(days=1)
        W_curr = np.array([curr])
        W_fin = np.array([curr - timedelta(days=7)])
        W_sig = np.array([new_york_offset(curr + timedelta(days=8))])
        chars = np.empty(W_sig.size, dtype='<U3')
        chars[:] = 'W1'
        arr = np.array([W_curr, W_fin, W_sig, chars])
        return np.column_stack(arr) 

    def _find_else_signal(self, base, d, tf):
        """ Minutely and daily signals """
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

    def _place_signals_into_queue(self, signals_found):
        """ Signals will be place into the queue """
        for s in signals_found:
            signal_event = SignalEvent(
                finished_bar=s[1],
                current_bar=s[0],
                next_bar=s[2],
                timeframe=s[3]
            )
            self.events_queue.put(signal_event)
        
    def generate_signals(self):
        """ 
        Compare the current time with the signal, any signal
        that is less than the current time will be placed into the
        queue.
        """
        self.cur_time = datetime.utcnow()
        signals_found = self.signals[self.signals[:,0] <= self.cur_time]
        self.signals = self.signals[self.signals[:,0] > self.cur_time]
        self._place_signals_into_queue(signals_found)
