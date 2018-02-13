from subprocess import Popen, PIPE
from threading import Thread
from queue import Queue
import time


class SubprocessHandler(object):
    def __init__(self, events_queue):
        self._events_queue = events_queue
        self.process = {}

    def _send_job_to_subprocess(self, sumting, job):
        p = self.process[sumting]['process']
        p.stdin.write('%s\n' % job)

    def initialise_sub(self, sumting):
        sub = Popen(['python3', 'fx_collect/stdout_test.py'],
            stdin=PIPE, stdout=PIPE,
            shell=False, bufsize=0,
            universal_newlines=True)
        nbsr = SubprocessQueue(
            sub.stdout, self._events_queue)
        sub_attribs = {
            'process': sub,
            'pipe': nbsr}
        self.process[sumting] = sub_attribs

    def on_collect(self, event):
        jobno = str(event[0])
        sumting = str(event[1])
        if sumting not in self.process:
            self.initialise_sub(sumting)
        job = '{0}, {1}'.format(
            jobno, sumting)
        self._send_job_to_subprocess(sumting, job)

class SubprocessQueue(object):
    def __init__(self, stream, events_queue):
        self._s = stream
        self._q = events_queue
        def _streamQueue(s, q):
            while True:
                response = s.readline()
                if response:
                    q.put(response)

        self._t = Thread(target=_streamQueue,
            args=(self._s, self._q,))
        self._t.daemon = True
        self._t.start()
        
from datetime import datetime
q = Queue()
s = SubprocessHandler(q)


while True:
    for jobno in range(200):
        event = jobno, jobno*10
        s.on_collect(event)
    time.sleep(60)
    
