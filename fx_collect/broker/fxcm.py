from forexconnect import ForexConnectHistoryClient, ForexConnectOffersClient
from .base import AbstractBroker

from datetime import datetime, timedelta

import numpy as np
import time


class FXCMBrokerHistory(AbstractBroker):
    """
    The FXCMBrokerHistory object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """
    def __init__(self, user, passwd, env, url):
        self.broker = 'fxcm'
        self._u = user
        self._p = passwd
        self._e = env
        self._url = url
        self._dt = np.dtype(
            [
                ('date', '<M8[us]'), ('askopen', '<f8'),
                ('askhigh', '<f8'), ('asklow', '<f8'),
                ('askclose', '<f8'), ('bidopen', '<f8'),
                ('bidhigh', '<f8'), ('bidlow', '<f8'),
                ('bidclose', '<f8'), ('volume', '<i8')
            ]
        )
        self._login_()
        
    def _login_(self):
        self._session = ForexConnectHistoryClient(
                self._u, self._p, self._e, self._url
        )

    def get_open_datetime(self, offer):
        """
        Tries to determine what time the market opened for a given 
        offer by returning the earliest minutely datetime value
        of the trading current day.
        """
        dt = datetime.utcnow().replace(second=0,microsecond=0)
        utc_now = dt 
        midnight = dt.replace(hour=0,minute=0)
        jobs = []
        rng = np.arange(midnight, utc_now, dtype='datetime64[m]')
        points = rng[0::200]
        for i in np.arange(len(points)):
            fm = points[i].item()
            try:
                to = (points[i+1] - 1).item()
            except IndexError:
                to = utc_now
            jobs.append((fm,to))
        for i in jobs:
            data = self._get_bars(
                offer, 'm1', i[0], i[1])
            if len(data) > 0:
                break
        return self._fm_ole(data[-1].date)

    def current_tradingweek(self):
        """Takes the latest daily bar date time to setup
        initial system dates."""
        init_dt = self.get_initial_datetime('GBP/USD')
        if init_dt.weekday() == 6: # Its Sunday
            wk_str = init_dt
        else:
            wk_str = init_dt - timedelta(days=init_dt.weekday()+1)
        wk_end = wk_str + timedelta(days=5)
        return wk_str, wk_end

    def get_initial_datetime(self, offer):
        """Gets the current Daily bar date time"""
        bars = self._get_bars(
            offer, 'D1', datetime.utcnow()-timedelta(days=14),
            datetime.utcnow()
        )
        return bars[0].date

    def _get_bars(self, offer, time_frame, dtfm, dtto):
        return self._session.get_historical_prices(
            offer.encode(),
            self._to_ole(dtfm),
            self._to_ole(dtto),
            time_frame.encode()
        )

    def _bars(self, offer, time_frame, dtfm, dtto):
        """
        Gets price data from FXCM, converts to a numpy array
        and performs a basic integrity check
        """
        fxdata = self._get_bars(offer, time_frame, dtfm, dtto)
        a = np.array(
            [v.__getinitargs__() for v in fxdata], dtype=self._dt
        )
        a = a[a['askhigh'] >= a['asklow']]
        a = a[a['askhigh'] >= a['askopen']]
        a = a[a['asklow'] <= a['askopen']]
        a = a[a['askhigh'] >= a['askclose']]
        a = a[a['asklow'] <= a['askclose']]
        a = a[a['bidhigh'] >= a['bidlow']]
        a = a[a['bidhigh'] >= a['bidopen']]
        a = a[a['bidlow'] <= a['bidopen']]
        a = a[a['bidhigh'] >= a['bidclose']]
        a = a[a['bidlow'] <= a['bidclose']]
        a = a[a['volume'] >= 0]
        idx = np.unique(a['date'][::-1], return_index=True)[1]
        return a[::-1][idx][::-1]

    def data_collection(
        self, offer, time_frame, dtfm, dtto
    ):
        """
        """
        if isinstance(dtfm, str):
            dtfm = datetime.strptime(dtfm, '%Y-%m-%d %H:%M')
        if isinstance(dtto, str):
            dtto = datetime.strptime(dtto, '%Y-%m-%d %H:%M')
        f = self._to_ole
        if dtfm < dtto:
            while (f(dtto) - f(dtfm)) > 0.0001:
                if self._session_status():
                    data = self._bars(
                       offer, time_frame, dtfm, dtto
                    )             
                    if len(data) > 0:
                        nxt_dt = data['date'].min().item()
                        if abs(f(dtto) - f(nxt_dt)) > 0.0001:
                            dtto = nxt_dt
                        else:
                            break
                        yield data.tolist()
                    else:
                        break
                else:
                    self._login_()   


class FXCMBrokerOffers(AbstractBroker):
    """
    The FXCMBrokerOffers object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """
    def __init__(self, user, passwd, env, url):
        self.broker = 'fxcm'
        self._u = user
        self._p = passwd
        self._e = env
        self._url = url
        self.supported_timeframes = [
            'm1', 'm5', 'm15', 'm30',
            'H1', 'H2', 'H4', 'H8',
            'D1', 'W1', 'M1'
              
        ]
        self._login_()

    def _login_(self):
        self._session = ForexConnectOffersClient(
            self._u, self._p, self._e, self._url
        )

    def get_offers(self):
        return self._session.get_offers()

    def get_market_status(self, offer):
        while True:
            status = self._session.get_offer_trading_status(offer)
            if status is not 'U':
                break
        return status
        
    def get_offer_timestamp(self, offer):
        while True:
            timestamp = self._session.get_offer_time(offer)
            if timestamp is not 0.0:
                break
        return timestamp

    def get_point_size(self, offer):
        return self._session.get_offer_point_size(offer)

    def get_base_currency(self, offer):
        return self._session.get_contract_currency(offer)
        
    def get_passport(self, o):
        return (
            self.supported_timeframes,
            self.get_point_size(o),
            self.get_base_currency(o)
        )
            
    def get_status(self, offers):
        """
        Returns current markets status ie OPEN or CLOSED and
        the last update
        """
        offers_dict = {}
        for o in offers:
            offers_dict[o] = {
                'status': self.get_market_status(o),
                'timestamp': self._fm_ole(self.get_offer_timestamp(o))
            }
        return offers_dict 

    def get_current_bid_ask(self, offer):
        """Return the current BID and ASK values"""
        while True:
            try:
                bid, ask = self._session.get_bid_ask(offer)
                if bid > 0 and ask > 0:
                    break
            except RuntimeError as e:
                # Only happens when market Open or Closes
                pass
        return bid, ask

