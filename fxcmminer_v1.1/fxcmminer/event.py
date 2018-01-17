import logging

class Event(object):
    @property
    def typename(self):
        return self.type

class OfferEvent(Event):
    def __init__(self, fxoffers, time_frames):
        self.type = 'OFFER'
        self.fxoffers = fxoffers
        self.time_frames = time_frames
    def __str__(self):
        return "Type: %s, Offers: %s, TimeFrame: %s" % (
            str(self.type), str(self.fxoffers),
            str(self.time_frames)
        )

    def __repr__(self):
        return str(self)

class CleanedDataEvent(Event):
    def __init__(self, data, instrument, time_frame):
        self.type = 'CLEANED'
        self.data = data
        self.instrument = instrument
        self.time_frame = time_frame

    def __str__(self):
        return "Type: %s, Data: %s, Instrument : %s, Time Frame : %s" % (
            str(self.type), str(self.data),
            str(self.instrument), str(self.time_frame)
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
            str(self.type), str(self.data),
            str(self.instrument), str(self.time_frame)
        )

    def __repr__(self):
        return str(self)

class LiveReadyEvent(Event):
    def __init__(self, offer):
        self.type = 'LIVEREADY'
        self.offer = offer

    def __str__(self):
        return "Type: %s, Atrr: %s" % (
            str(self.type), str(self.offer)
        )

    def __repr__(self):
        return str(self)

class GetLiveEvent(Event):
    def __init__(self, time_frame):
        self.type = 'GETLIVE'
        self.time_frame = time_frame

    def __str__(self):
        return "Type: %s, Atrr: %s" % (
            str(self.type), str(self.time_frame)
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
            str(self.type), str(self.data),
            str(self.instrument), str(self.time_frame)
        )

    def __repr__(self):
        return str(self)
