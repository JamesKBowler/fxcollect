from datetime import datetime, timedelta

class Instrument(object):
    def __init__(
        self, broker, instrument, time_frame, market_status, last_update, dt
    ):
        trading_wk_str = dt - timedelta(days=dt.weekday()+1)
        self.sw_hour = trading_wk_str.hour
        self.td = trading_wk_str.hour - 22
        # Passport
        self.instrument = instrument
        self.time_frame = time_frame
        self.market_status = market_status
        self.last_update = last_update
        self.db_min = None
        self.db_max = None
        self.fin_bar = None

    def update(self, lastupdate, market_status):
        self.last_update = lastupdate
        self.market_status = market_status
      
    def calculate_finished_bar(self):
        """
        Create time delta resolution for finding the 
        last finished bar published by FXCM. This is to stop
        unfinished bars being written to the database.
        """
        lu = self.last_update.replace(second=0,microsecond=0)
        t = int(self.time_frame[1:])

        if self.time_frame[:1] == "m" or self.time_frame[:1] == "H":
            variable_selection = {
                'm':[lu, 1*t, lu.minute, 'minutes'],
                'H':[lu.replace(minute=0), 1*t, lu.hour, 'hours']}
            d = variable_selection[self.time_frame[:1]]
            init_bar, delta, res, interval_type = d[0],d[1],d[2],d[3]
            m = ( res // delta + 0) * delta
            finished_bar = (
                init_bar + timedelta(**{interval_type:(m-res)-t})
            ) - timedelta(hours=self.td)

        elif self.time_frame[:1] == "D":
            init_bar = lu.replace(hour=self.sw_hour, minute=0)
            finished_bar = init_bar - timedelta(days=t)
        
        self.fin_bar = finished_bar