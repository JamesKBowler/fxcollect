from .subprocess_reader import SubprocessReader
from subprocess import Popen, PIPE
from termcolor import cprint


class SubprocessEngine(object):
    """
    A class that keeps track of, and communicates
    to all subprocess instances.
    
    
    """
    def __init__(self, events_queue):
        self._events_queue = events_queue
        self.process = {}

    def kill_process(self, offer=None):
        killed = []
        if offer is None:
            kills = self.process
        else:
            kills = [offer]
        for s in kills:
            self._send_job_to_subprocess(s, "X, X")
            killed.append(s)
            self.process[s]['process'].kill()
        [self.process.pop(i) for i in killed]

    def initialise_offer(self, offer):
        sub = Popen(['python3', 'fx_collect/subprocess_worker.py', offer],
            stdin=PIPE,stdout=PIPE,
            shell=False, bufsize=0,
            universal_newlines=True
        )
        ssr = SubprocessReader(
            identifer=offer,
            stream=sub.stdout,
            events_queue=self._events_queue,
            expected=3,
            log=True,
            option='stdout'
        )
        self.process[offer] = {
            'process': sub,
            'pipe': ssr
        }

    def _send_job_to_subprocess(self, offer, job):
        """
        Communicate with subprocess.
        """
        p = self.process[offer]['process']
        p.stdin.write('%s\n' % job)

    def on_collect(self, event):
        cprint(event, 'green')
        jobno = event.jobno
        offer = event.offer
        time_frame = event.timeframe
        dtfm = event.dtfm
        dtto = event.dtto
        if offer not in self.process:
            self.initialise_offer(offer)
        job = '{0}, {1}, {2}, {3:%Y-%m-%d %H:%M}, {4:%Y-%m-%d %H:%M}'.format(
            jobno, offer, time_frame, dtfm, dtto)
        self._send_job_to_subprocess(offer, job)