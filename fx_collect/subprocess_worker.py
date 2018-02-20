from database.mariadb import Database
from broker.fxcm.session import FXCMBroker
from threading import Thread
from queue import Queue, Empty
from subprocess_reader import SubprocessReader
import sys
import time


class SubprocessWorker(object):
    def __init__(self, offer):
        self._s = input
        self._q = Queue()
        self._o = offer
        self._broker = FXCMBroker(
            offers_table=False,
            market_data=True,
            trading=False
        ).market_data
        self._database = Database(self._broker.whoami())
        self._sir = SubprocessReader(
            identifer=self._o,
            stream=self._s,
            events_queue=self._q,
            expected=5,
            log=False,
            option='input'
        )
        self._queue_stream()

    def _queue_stream(self):
        while True:
            try:
                try:
                    job_event = self._q.get(False)
                except Empty:
                    time.sleep(0.01)
                else:
                    if isinstance(job_event, list):
                        self._on_data_request(job_event)
                    else:
                        if job_event is 'KILL':
                            self._send_message(
                                'K',self._o,'K'
                            )
                            break
                        else: # EXCEPTION
                            self._send_message(
                                'E',self._o,'E'
                            )
                            break
            except KeyboardInterrupt:
                break
        if self._broker.is_connected():
            self._broker._logout_session()

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

    def _on_data_request(self, job_event):
        jobno, offer, timeframe, dtfm, dtto = job_event
        # Contact broker for data
        data_gen = self._price_data_collection(
            offer, timeframe, dtfm, dtto)
        # Write data to database
        self._write_to_database(
            offer, timeframe, data_gen)
        # Respond back to the main process once finished.
        self._send_message(
            jobno, offer, timeframe)

offer = sys.argv[1]
s = SubprocessWorker(offer)