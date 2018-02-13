from threading import Thread
from queue import Queue, Empty
import sys
import time
import numpy as np
from broker.fxcm import FXCMBrokerHistory
from datetime import datetime, timedelta

class SubprocessWorker(object):
    def __init__(self):
        self._s = input
        self._q = Queue()
        self._b = FXCMBrokerHistory()
        def _stdout_stream(s, q):
            while True:
                line = s()
                if line:
                    event = line.strip().split(', ')
                    q.put(event)
                else:
                    q.put('EXCEPTION')

        self._t = Thread(target =_stdout_stream,
                args = (self._s, self._q,))
        self._t.daemon = True
        self._t.start()
        self._queue_stream()

    def _send_message(self, jobno, sumting):
        msg = "{}, {}\n".format(jobno, sumting)
        sys.stdout.write(msg)
        sys.stdout.flush()

    def _queue_stream(self):
        while True:
            try:
                signal = self._q.get(False)
            except Empty:
                time.sleep(0.01)
            else:
                if isinstance(signal, list):
                    self._on_signal(signal)
                else:
                    pass
        
    def _on_signal(self, signal):
        jobno, sumting = signal
        # Extract variables from signal
        dt = self._b._get_bars(
            'GBP/USD', 'm1', datetime(2018,2,8,21,37), datetime(2018,2,8,21,40))[0].date
        dts = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        # Respond back to the main process once finished.
        self._send_message(jobno, dts)

SubprocessWorker()
        