class InstrumentAttributes(object):
    def __init__(
        self, broker, instrument, time_frames,
        market_status, last_update, utc_now, wk_str, wk_end
    ):
        # Start of Trading Week
        self.utc_now = utc_now
        self.wk_str = wk_str
        self.wk_end = wk_end
        self.str_hour = wk_str.hour
        self.td = wk_str.hour - 22
        # Passport
        self.instrument = instrument
        self.market_status = market_status
        self.last_update = last_update
        self.time_frames = time_frames
        # Time frame storage dict
        self.attrib = {}
        for time_frame in time_frames:
            self.attrib[time_frame] = {
              'db_min' : None,
              'db_max' : None,
              'finbar' : None
            }

    def update_instrument_status(
        self, lastupdate, market_status, utc_now
    ):
        self.utc_now = utc_now
        self.last_update = lastupdate
        self.market_status = market_status

    def _update_database_datetime(
        self, time_frame, pdfm, pdto
    ):
        if pdfm < self.attrib[time_frame]['db_min']: 
            self.attrib[time_frame]['db_min'] = pdfm
        if pdto >= self.attrib[time_frame]['db_max']:
            self.attrib[time_frame]['db_max'] = pdto
