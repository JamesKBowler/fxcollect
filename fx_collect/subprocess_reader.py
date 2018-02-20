from threading import Thread
from collections import namedtuple
try:
    from .event import ResponseEvent
except (SystemError, ValueError, ImportError):
    from event import ResponseEvent


class AbstractSubprocessReader(object):
    def input_reader(self, stream):
        return stream()
        
    def input_container(self, result):
        return result
        
    def input_exception(self, result, o):
        return False
            
    def stdout_reader(self, stream):
        return stream.readline()
        
    def stdout_container(self, result):
        jobno, offer, time_frame = result
        return ResponseEvent(
            int(jobno),  # ValueError
            offer,
            time_frame
        )
    def std_out_exception(self, result, o):
        if result[0] is 'E':
            print_console("{} Exception".format(o))
            return True
        elif result[0] is 'K':
            print_console("{} killed".format(o))
            return True

    def print_console(self, msg):
        if self.logging_on:
            print("SubprocessReader {}".format(msg))


class SubprocessReader(AbstractSubprocessReader):
    """
    A class representing a SubprocessReader.
    It contains an id for tracking with the ability
    to handle different types of streamed events.

    Parameters
    ----------
    identifier : int
        The human-readable identifier
    stream: input | stdout
        Stream to read
    expected : int, length of stream
        Length of message in stream
    log: bool
        Turns printing on/off
    option : 'stdout' or 'input'    
        The SubprocessReader will read from the subprocess
        sys.stdout or input() stream and feed these back
        into the parent process events queue.
    """
    def __init__(
        self, identifer, 
        stream, events_queue,
        expected, log=False, option='input'
    ):
        self.id = identifer
        self._s = stream
        self._q = events_queue
        self._e = expected
        self.logging_on = log
        self._l = self.print_console
        if option == 'input':
            self._r = self.input_reader
            self._c = self.input_container
            self._ex = self.input_exception
        elif option == 'stdout':
            self._r = self.stdout_reader
            self._c = self.stdout_container
            self._ex = self.std_out_exception
            
        def _stream_to_queue(
            id, stream, reader, container,
            events_queue, expected, logger,
            exception
        ):
            """
            Stream reading.
            """                    
            while True:
                try:
                    result = reader(stream).strip().split(', ')
                    if len(result) == expected:
                        try:
                            event = container(result)
                            events_queue.put(event)
                        except ValueError:
                            if exception(result, id):
                                break
                    else:
                        break
                except EOFError:
                    break
            logger("{} stopped".format(id))

        self.t = Thread(
            target=_stream_to_queue,
            args=(
                self.id,
                self._s,
                self._r,
                self._c,
                self._q,
                self._e,
                self._l,
                self._ex,
            )
        )
        self.t.daemon = True
        self.t.start()
        