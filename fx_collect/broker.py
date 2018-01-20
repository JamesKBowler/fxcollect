from settings import FX_USER, FX_PASS, URL, FX_ENVR
from datetime import datetime, timedelta

import forexconnect as fx
import numpy as np
import time


class FXCMBrokerHandler(object):
    """
    The BrokerHandler object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """
    def __init__(self):
        self.broker = 'fxcm'
        # self.supported_time_frames = [
        #     'm1', 'm5', 'm15', 'm30',
        #     'H1', 'H2', 'H4', 'H8',
        #     'D1'
        # ]
        self.supported_time_frames = [
            'D1',
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
                    FX_USER,
                    FX_PASS,
                    FX_ENVR,
                    URL
                )
                if self._session_status():
                    break
            except RuntimeError: time.sleep(1)
        if not self.session.is_connected():
            raise Exception('Unable to login')

    def _get_instruments(self):
        return self.session.get_offers()

    def _get_status(self, offer=None):
        def ole(o):
            OLE_TIME_ZERO = datetime(1899, 12, 30, 0, 0, 0)
            return OLE_TIME_ZERO + timedelta(days=float(o))
        d = {}
        d1 = self.session.get_market_status()
        d2 = self.session.get_time()
        for k in d1.keys():
            d[k] = (d1[k], ole(d2[k]))
        if offer is not None:
            return d[offer]
        else: return d

    def _init_datetime(self, offer):
        return self.session.get_historical_prices(
            offer,
            datetime.utcnow(),
            datetime(1899, 12, 30, 0, 0, 0),
            'D1'
        )[0].date

    def _get_next_tick(self, offer):
        bid = self.session.get_bid(offer)
        ask = self.session.get_ask(offer)
        return bid, ask

    def _get_bars(
        self, offer, time_frame, dtfm, dtto
    ):
        fxdata =  self.session.get_historical_prices(
            offer, dtfm, dtto, time_frame
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
