from subprocess import Popen, PIPE
from threading import Thread
from queue import Queue
from .event import ResponseEvent
from termcolor import cprint
import time


class SubprocessEngine(object):
    def __init__(self, config, events_queue):
        self._config = config
        self._events_queue = events_queue
        self.process = {}

    def _send_job_to_subprocess(self, offer, job):
        p = self.process[offer]['process']
        p.stdin.write('%s\n' % job)

    def kill_process(self, offer=None):
        killed = []
        if offer is None:
            kills = self.process
        else:
            kills = [offer]
        for s in kills:
            self._send_job_to_subprocess(s, "X, X")
            time.sleep(0.5)
            killed.append(s)
            self.process[s]['process'].kill()
        [self.process.pop(i) for i in killed]

    def initialise_offer(self, offer):
        sub = Popen(['python3', 'fx_collect/worker.py'],
            stdin=PIPE,stdout=PIPE,
            shell=False, bufsize=0,
            universal_newlines=True
        )
        nbsr = SubprocessQueue(
            sub.stdout, self._events_queue, offer)
        sub_attribs = {
            'process': sub,
            'pipe': nbsr}
        self.process[offer] = sub_attribs
        time.sleep(1)

    def on_collect(self, event):
        cprint(event, 'green')
        jobno = event.jobno
        offer = event.offer
        time_frame = event.timeframe
        dtfm = event.dtfm
        dtto = event.dtto
        if offer not in self.process:
            self.initialise_offer(offer)
            cprint("{}: Started".format(offer), 'magenta')
        job = '{0}, {1}, {2}, {3:%Y-%m-%d %H:%M}, {4:%Y-%m-%d %H:%M}'.format(
            jobno, offer, time_frame, dtfm, dtto)
        self._send_job_to_subprocess(offer, job)

class SubprocessQueue(object):
    def __init__(self, stream, events_queue, offer):
        self._s = stream
        self._q = events_queue
        self._o = offer
        def _streamQueue(s, q, o):
            while True:
                res = s.readline()
                if res:
                    jobno, offer, time_frame = res.strip().split(', ')
                    try:
                        event = ResponseEvent(
                            int(jobno),
                            offer,
                            time_frame
                        )
                        q.put(event)
                    except ValueError:
                        if jobno is 'E':
                            print("Subprocess {} Exception".format(o))
                            break
                        elif jobno is 'K':
                            print("Subprocess {} killed".format(o))
                            break
                else:
                    print("SubprocessQueue._streamQueue {} failed".format(o))
                    break

        self._t = Thread(target=_streamQueue,
            args=(self._s, self._q, self._o,))
        self._t.daemon = True
        self._t.start()