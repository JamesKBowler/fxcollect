from enum import Enum


EventType = Enum("EventType", "SIGNAL GETDATA RESPONSE")


class Event(object):
    """
    """
    @property
    def typename(self):
        return self.type.name


class SignalEvent(Event):
    """
    """
    def __init__(
        self, finished_bar, current_bar,
        next_bar, timeframe
    ):
        self.type = EventType.SIGNAL
        self.finished_bar = finished_bar
        self.current_bar = current_bar
        self.next_bar = next_bar
        self.timeframe = timeframe

    def __str__(self):
        return "Type: %s, Fin: %s, Curr: %s, Next: %s, Time Frame: %s" % (
            str(self.type), str(self.finished_bar),
            str(self.current_bar), str(self.next_bar),
            str(self.timeframe)
        )

    def __repr__(self):
        return str(self)


class DataEvent(Event):
    """
    """
    def __init__(
        self, jobno, offer, timeframe,
        dtfm, dtto
    ):
        self.type = EventType.GETDATA
        self.jobno = jobno
        self.offer = offer
        self.timeframe = timeframe
        self.dtfm = dtfm
        self.dtto = dtto

    def __str__(self):
        return "Type: %s, ID: %s, Offer: %s Time Frame: %s, FROM: %s, TO: %s" % (
            str(self.type), str(self.jobno),
            str(self.offer), str(self.timeframe),
            str(self.dtfm), str(self.dtto)
        )

    def __repr__(self):
        return str(self)


class ResponseEvent(Event):
    """
    """
    def __init__(
        self, jobno, offer, timeframe
    ):
        self.type = EventType.RESPONSE
        self.jobno = jobno
        self.offer = offer
        self.timeframe = timeframe

    def __str__(self):
        return "Type: %s, ID: %s, Offer: %s Time Frame: %s" % (
            str(self.type), str(self.jobno),
            str(self.offer), str(self.timeframe)
        )

    def __repr__(self):
        return str(self)