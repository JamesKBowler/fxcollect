from settings import FX_USER, FX_PASS, URL, FX_ENVR
from datetime import datetime, timedelta

import forexconnect as fx
import numpy as np
import time

OLE_TIME_ZERO = datetime(1899, 12, 30)

class FXCMBrokerHandler(object):
    """
    The BrokerHandler object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """
    def __init__(self):
        self.broker = 'fxcm'
        self.supported_time_frames = [
            'D1', 'W1', 'M1',
            'H8', 'H4', 'H2', 'H1',
            'm30', 'm15', 'm5', 'm1'
        ]
        self.dtype = np.dtype(
            [
                ('date', '<M8[us]'), ('askopen', '<f8'),
                ('askhigh', '<f8'), ('asklow', '<f8'),
                ('askclose', '<f8'), ('bidopen', '<f8'),
                ('bidhigh', '<f8'), ('bidlow', '<f8'),
                ('bidclose', '<f8'), ('volume', '<i8')
            ]
        )
        self._login()

    def _session_status(self):
        if self.session.is_connected():
            return True
        else: return False

    def _login(self):
        con = False
        while True:
            try:
                self.session = fx.ForexConnectClient(
                    FX_USER, FX_PASS,
                    FX_ENVR, URL
                )
                if self._session_status():
                    con = True
                    break
            except RuntimeError: time.sleep(1)
        if not con:
            raise Exception('Unable to login')
            
    def get_offers(self):
        return self.session.get_offers()

    def get_offer_status(self, offer):
        status = self.session.get_offer_trading_status(offer)
        oletime = self.session.get_offer_time(offer)
        return status, self._from_ole(oletime) 

    def get_initial_datetime(self, offer):
        return self.session.get_historical_prices(
            offer, 0, 0, 'D1')[0].date

    def get_open_datetime(self, offer):
        dt = datetime.utcnow().replace(second=0,microsecond=0)
        dtto = self._to_ole(dt)
        dtfm = self._to_ole(dt.replace(hour=0,minute=0))
        while True:
            data = self.session.get_historical_prices(
                offer, dtfm, dtto, 'm1')
            if len(data) > 0:
                dtto = self._to_ole(data[-1].date)
                if len(data) == 1:
                    break
            else:
                break
        return self._from_ole(dtto)

    def get_current_tick(self, offer):
        bid = self.session.get_bid(offer)
        ask = self.session.get_ask(offer)
        return bid, ask
      
    def get_bars(self, offer, time_frame, dtfm, dtto):
        fxdata =  self.session.get_historical_prices(
            offer,
            self._to_ole(dtfm),
            self._to_ole(dtto),
            time_frame
        )
        npvalues = self._numpy_convert(fxdata)
        return self._integrity_check(npvalues)
      
    def _numpy_convert(self, values):
        return np.array(
            [v.__getinitargs__() for v in values], dtype=self.dtype)
  
    def _integrity_check(self, a):
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
        idx = np.unique(a['date'][::-1], return_index = True)[1]
        return a[::-1][idx][::-1]

    def _to_ole(self, pydate):
        delta = pydate - OLE_TIME_ZERO
        return float(delta.days) + (float(delta.seconds) / 86400)

    def _from_ole(self, oletime):
        return OLE_TIME_ZERO + timedelta(days=float(oletime))
