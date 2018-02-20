class Offer(object):
    def __init__(
        self, broker, offer, timeframes, market_open,
        point_size, init_timestamp, contract_currency
    ):
        # Passport
        self.broker = broker
        self.offer = offer
        self.timeframes = timeframes
        self.point_size = point_size
        self.contract = contract_currency
        # Start as market closed
        self.status = 'C'
        self.timestamp = init_timestamp
        # Record when the market opened for the day
        self.market_open = market_open
        # Current Ticks
        self.bid = None
        self.ask = None
        # Time frame storage dict
        self.attribs = {}
        for timeframe in timeframes:
            self.attribs[timeframe] = {
                'db_min' : None,
                'db_max' : None,
                'finbar' : None,
                'busy' : True,
                'jobno': -2,
                'penalty' : 0
            }

    def update_job_number(self, timeframe, jobno):
        self.attribs[timeframe]['jobno'] = jobno + 1

    def penalty(self, timeframe, clear=False):
        if not clear:
            self.attribs[timeframe]['penalty'] += 1
            if self.attribs[timeframe]['penalty'] > 5:
                return True
            else:
                return False
        else:
            self.attribs[timeframe]['penalty'] = 0

    def mark_as_busy(self, timeframe, busy):
        self.attribs[timeframe]['busy'] = busy

    def return_job(self, timeframe):
        dtfm = self.attribs[timeframe]['db_max']
        jobno = self.attribs[timeframe]['jobno']
        return jobno, dtfm

    def signal_valid(self, signal, current_bar, timeframe):
        att = self.attribs[timeframe]
        if self.status == 'O':
            if att['busy'] == False:
                if signal > att['db_max']:
                    if current_bar > self.market_open:
                        return True
        return False

    def update_offer(
        self, timestamp, market_status, bid, ask
    ):
        self.status = market_status
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask

    def update_datetime(
        self, timeframe, db_min, db_max
    ):
        self.attribs[timeframe]['db_min'] = db_min
        self.attribs[timeframe]['db_max'] = db_max

    def create_snapshot(self):
        attribs = {}
        for k, v in self.attribs.items():
            attribs[k] = {
                'db_min' : v[
                    'db_min'].strftime('%Y/%m/%d %H:%M:%S'),
                'db_max' : v[
                    'db_max'].strftime('%Y/%m/%d %H:%M:%S')
            }
        return {
            self.offer : {
                'point_size' : self.point_size,
                'market_status' : self.status,
                'base' : self.contract,
                'last_update' : self.timestamp.strftime(
                    '%Y/%m/%d %H:%M:%S.%f'),
                'bid' : self.bid,
                'ask' : self.ask,
                'time_frames' : attribs
            }
        }
