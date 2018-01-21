class InstrumentAttributes(object):
    def __init__(
        self, broker, instrument, time_frames,
        market_status, last_update, utc_now,
        wk_str, wk_end
    ):
        # Passport
        self.instrument = instrument
        self.market_status = market_status
        self.last_update = last_update
        self.time_frames = time_frames
        # Start of Trading Week
        self.utc_now = utc_now
        self.wk_str = wk_str
        self.wk_end = wk_end
        self.str_hour = wk_str.hour
        self.td = wk_str.hour - 22
        # Ticks
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

    def update_instrument_status(
        self, last_update, market_status,
        utc_now, bid, ask
    ):
        self.utc_now = utc_now
        self.last_update = last_update
        self.market_status = market_status
        self.bid = bid
        self.ask = ask

    def update_database_datetime(
        self, time_frame, pdfm, pdto
    ):
        if pdfm < self.ttribs[time_frame]['db_min']: 
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
                 'utc_now' : self.utc_now.strftime(
                    '%Y/%m/%d %H:%M:%S.%f'),
                 'wk_str' : self.wk_str.strftime(
                    '%Y/%m/%d %H:%M:%S'),
                 'wk_end' : self.wk_end.strftime(
                    '%Y/%m/%d %H:%M:%S'),
                 'market_status' : self.market_status,
                 'last_update' : self.last_update.strftime(
                    '%Y/%m/%d %H:%M:%S.%f'),
                 'bid' : self.bid,
                 'ask' : self.ask,
                 'time_frames' : attribs
            }
        }
