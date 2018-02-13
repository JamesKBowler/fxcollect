from settings import DB_HOST, DB_USER, DB_PASS, FX_USER, FX_PASS, FX_ENVR, URL
from database.mariadb import Database
from broker.fxcm import FXCMBrokerHistory
from threading import Thread
from queue import Queue, Empty

import sys
import time


class SubprocessWorker(object):
    def __init__(self):
        self._s = input
        self._q = Queue()
        self._o = None
        self._database = Database(
            'fxcm', DB_HOST, DB_USER, DB_PASS
        )
        self._broker = FXCMBrokerHistory(
            FX_USER, FX_PASS, FX_ENVR, URL
        )
        
    def start(self):    
        def _stdout_stream(s, q):
            while True:
                line = s()
                if line:
                    event = line.strip().split(', ')
                    if event[0] is not 'X':
                        q.put(event)
                    elif event[0] is 'X':
                        q.put('KILL')
                        break
                else:
                    q.put('EXCEPTION')
                    break

        self._t = Thread(target=_stdout_stream,
                args = (self._s, self._q,))
        self._t.daemon = True
        self._t.start()
        self._queue_stream()

    def _price_data_collection(
        self, offer, timeframe, dtfm, dtto
    ):
        return self._broker.data_collection(
            offer, timeframe, dtfm, dtto
        )

    def _write_to_database(
        self, offer, timeframe, data_gen
    ):
        for data in data_gen:
            self._database.write(offer, timeframe, data)

    def _send_message(
        self, jobno, offer, timeframe
    ):
        msg = "{0}, {1}, {2}\n".format(jobno, offer, timeframe)
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
                    if signal is 'KILL':
                        self._send_message(
                            'K',self._o,'K'
                        )
                        break
                    else: # EXCEPTION
                        self._send_message(
                            'E',self._o,'E'
                        )
                        break
        self._broker._logout()

    def _on_signal(self, signal):
        # Extract variables from signal
        jobno, offer, timeframe, dtfm, dtto = signal
        if int(jobno) == -2:
            self._o = offer

        # Contact broker for data
        data_gen = self._price_data_collection(
            offer, timeframe, dtfm, dtto
        )
        # Write data to database
        self._write_to_database(
            offer, timeframe, data_gen
        )
        # Respond back to the main process once finished.
        self._send_message(
            jobno, offer, timeframe
        )

s = SubprocessWorker()
try:
    s.start()
except KeyboardInterrupt:
    s._broker._logout()
        