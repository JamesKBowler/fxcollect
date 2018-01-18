from datetime import datetime, timedelta

class Instrument(object):
    def __init__(
        self, broker, instrument, time_frame,
        market_status, last_update, dt
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

    def update(
        self, lastupdate, market_status
    ):
        self.last_update = lastupdate
        self.market_status = market_status
      
    def calculate_finished_bar(self):
        """
        Create time delta resolution for finding the 
        last finished bar published by FXCM. This is to stop
        unfinished bars being written to the database.
        """
        lu = self.last_update.replace(second=0,microsecond=0)
        tf = int(self.time_frame[1:])
        
        # New Your Offset
        if self.td % 2 == 0: nyo = 1
        else: nyo = 2
          
        if self.time_frame[:1] == "m":  # Minute
            ub = lu
            l = list(range(0,60,tf))
            cm = min(l, key=lambda x:abs(x-ub.minute))
            fin = ub.replace(minute=cm)-timedelta(minutes=tf)
            
        elif self.time_frame[:1] == "H":  # Hour
            ub = lu.replace(minute=0)
            h = ub.hour
            l = [e-nyo for e in [i + tf - 2 for i in list(range(1,25,tf))]]
            ch = min(l, key=lambda x:abs(x-h))
            fin = ub.replace(hour=ch)-timedelta(hours=tf)            

        elif self.time_frame[:1] == "D":  # Day
            init_bar = lu.replace(hour=self.sw_hour,minute=0)
            fin = init_bar - timedelta(days=tf)
            
        elif self.time_frame[:1] == "M":  # Month
            init_bar = lu.replace(day=1,hour=self.sw_hour,minute=0)
            fin = init_bar - timedelta(days=1)
        else:
            raise NotImplmented("Time-frame : %s Not Supported" % self.time_frame)
            
        self.fin_bar = fin
