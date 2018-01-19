from datetime import datetime, timedelta

class InstrumentAttributes(object):
    def __init__(
        self, broker, instrument, time_frames,
        market_status, last_update, dt
    ):
        # Start of Trading Week
        self.trading_wk_str = dt - timedelta(days=dt.weekday()+1)
        self.sw_hour = self.trading_wk_str.hour
        self.td = self.trading_wk_str.hour - 22
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
        self, lastupdate, market_status
    ):
        self.last_update = lastupdate
        self.market_status = market_status

    def _update_database_datetime(
        self, time_frame, pdfm, pdto
    ):
        if pdfm < self.attrib[time_frame]['db_min']: 
            self.attrib[time_frame]['db_min'] = pdfm
        if pdto >= self.attrib[time_frame]['db_max']:
            self.attrib[time_frame]['db_max'] = pdto

    def calculate_finished_bar(self, time_frame):
        """
        Stops unfinished bars from being written to the
        database by calculating the latest finshed bar.
        """
        lu = self.last_update.replace(second=0,microsecond=0)
        tf = int(time_frame[1:])
        # New York Offset
        if self.td % 2 == 0: nyo = 1
        else: nyo = 2
        if time_frame[:1] == "m":  # Minute
            adj = lu
            l = list(range(0,60,tf))
            cm = min(l, key=lambda x:abs(x-adj.minute))
            fin = adj.replace(minute=cm)-timedelta(minutes=tf)
        elif time_frame[:1] == "H":  # Hour
            adj = lu.replace(minute=0)
            l = [e-nyo for e in [i + tf - 2 for i in list(range(1,25,tf))]]
            ch = min(l, key=lambda x:abs(x-adj.hour))
            fin = adj.replace(hour=ch)-timedelta(hours=tf)            
        elif time_frame[:1] == "D":  # Day
            adj = lu.replace(hour=self.sw_hour,minute=0)
            fin = adj - timedelta(days=tf)
        elif time_frame[:1] == "M":  # Month
            adj = lu.replace(day=1,hour=self.sw_hour,minute=0)
            fin = adj - timedelta(days=1)
        else:
            raise NotImplmented("Time-frame : %s Not Supported" % time_frame)
        # Add Finished bar
        self.attrib[time_frame]['finbar'] = fin
