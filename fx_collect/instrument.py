class InstrumentAttributes(object):
    def __init__(
        self, broker, instrument, time_frames, last_update
    ):
        # Passport
        self.instrument = instrument
        self.market_status = 'C'
        self.last_update = last_update
        # Current Ticks
        self.bid = None
        self.ask = None
        # Time frame storage dict
        self.attribs = {}
        for time_frame in time_frames:
            self.attribs[time_frame] = {
                'db_min' : None,
                'db_max' : None,
                'finbar' : None
            }

    def update_instrument(
        self, last_update, bid, ask
    ):
        self.last_update = last_update
        self.bid = bid
        self.ask = ask

    def update_datetime(
        self, time_frame, pdfm, pdto
    ):
        if pdfm < self.attribs[time_frame]['db_min']: 
            self.attribs[time_frame]['db_min'] = pdfm
        if pdto >= self.attribs[time_frame]['db_max']:
            self.attribs[time_frame]['db_max'] = pdto
            
    def create_snapshot(self):
        attribs = {}
        for k, v in self.attribs.items():
            attribs[k] = {
                'db_min' : v[
                    'db_min'].strftime('%Y/%m/%d %H:%M:%S'),
                'db_max' : v[
                    'db_max'].strftime('%Y/%m/%d %H:%M:%S'),
                'finbar' : v[
                    'finbar'].strftime('%Y/%m/%d %H:%M:%S')
            }
        return {
            self.instrument : {
                 'market_status' : self.market_status,
                 'last_update' : self.last_update.strftime(
                        '%Y/%m/%d %H:%M:%S.%f'),
                 'bid' : self.bid,
                 'ask' : self.ask,
                 'time_frames' : attribs
            }
        }
