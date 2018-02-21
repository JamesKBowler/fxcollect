# The MIT License (MIT)
#
# Copyright (c) 2017 James K Bowler, Data Centauri Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


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

    def signal_valid(self, signal, current_bar, timeframe):
        att = self.attribs[timeframe]
        if self.status == 'O':
            if att['busy'] == False:
                if signal > att['db_max']:
                    if current_bar > self.market_open:
                        return True
        return False

    def update_broker_values(
        self, timestamp, market_status, bid, ask
    ):
        self.status = market_status
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask

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
