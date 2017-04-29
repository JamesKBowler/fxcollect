import logging


class Event(object):
    @property
    def typename(self):
        return self.type

class OfferEvent(Event):
    def __init__(self, fxoffer):
        self.type = 'OFFER'
        self.fxoffer = fxoffer

    def __str__(self):
        return "Type: %s, Atrr: %s" % (
            str(self.type), str(self.fxoffer)
        )

    def __repr__(self):
        return str(self)

class DBReadyEvent(Event):
    def __init__(self, fxoffer):
        self.type = 'DBREADY'
        self.fxoffer = fxoffer

    def __str__(self):
        return "Type: %s, Atrr: %s" % (
            str(self.type), str(self.fxoffer)
        )

    def __repr__(self):
        return str(self)

class HistDataEvent(Event):
    def __init__(self, data, instrument, time_frame):
        self.type = 'HISTDATA'
        self.data = data
        self.instrument = instrument
        self.time_frame = time_frame

    def __str__(self):
        return "Type: %s, Data: %s, Instrument : %s, Time Frame : %s" % (
            str(self.type), str(self.data), str(self.instrument), str(self.time_frame)
        )

    def __repr__(self):
        return str(self)

class LiveReadyEvent(Event):
    def __init__(self, offer):
        self.type = 'GETLIVE'
        self.offer = offer

    def __str__(self):
        return "Type: %s, Atrr: %s" % (
            str(self.type), str(self.offer)
        )

    def __repr__(self):
        return str(self)

class LiveDataEvent(Event):
    def __init__(self, data, instrument, time_frame):
        self.type = 'LIVEDATA'
        self.data = data
        self.instrument = instrument
        self.time_frame = time_frame

    def __str__(self):
        return "Type: %s, Data: %s, Instrument : %s, Time Frame : %s" % (
            str(self.type), str(self.data), str(self.instrument), str(self.time_frame)
        )

    def __repr__(self):
        return str(self)
