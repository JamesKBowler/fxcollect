import numpy as np
try:
    from fx_collect.utils.date_utils import fm_ole, to_ole
except ImportError:
    from utils.date_utils import fm_ole, to_ole
from datetime import datetime, timedelta
from .base import AbstractFXCMBroker

class FXCMOffersTable(AbstractFXCMBroker):
    """
    The FXCMBrokerOffers object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """
    def __init__(self):
        self._session = self._offers_table()

    def get_status(self, offers):
        """
        Returns current markets status ie OPEN or CLOSED and
        the last update
        """
        offers_dict = {}
        for o in offers:
            offers_dict[o] = {
                'status': self.get_market_status(o),
                'timestamp': self.get_offer_timestamp(o)
            }
        return offers_dict 

    def get_current_bid_ask(self, offer):
        """
        Return the current BID and ASK values
        """
        bid, ask = self._session.get_bid_ask(offer)
        if bid > 0 and ask > 0:
            return bid, ask
        return None, None

    def get_offers(self):
        """
        TODO Doc string.....
        """
        return self._session.get_offers()

    def get_market_status(self, offer):
        """
        TODO Doc string.....
        """
        status = self._session.get_offer_trading_status(offer)
        return status
        
    def get_offer_timestamp(self, offer):
        """
        TODO Doc string.....
        """
        timestamp = self._session.get_offer_time(offer)
        return fm_ole(timestamp)

    def get_point_size(self, offer):
        """
        TODO Doc string.....
        """
        return self._session.get_offer_point_size(offer)

    def get_base_currency(self, offer):
        """
        TODO Doc string.....
        """
        return self._session.get_contract_currency(offer)

    def get_passport(self, o):
        """
        TODO Doc string.....
        """
        return (
            self.supported_timeframes(),
            self.get_point_size(o),
            self.get_base_currency(o)
        )


class FXCMMarketData(AbstractFXCMBroker):
    """
    The FXCMMarketData object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """
    def __init__(self):
        self._session = self._market_data()
        
    def get_open_datetime(self, offer):
        """
        Tries to determine what time the market opened for a given 
        offer by returning the earliest minutely datetime value
        of the trading current day.
        """
        utc_now = datetime.utcnow().replace(second=0,microsecond=0)
        midnight = utc_now.replace(hour=0,minute=0)
        try:
            lowest_hour = self._get_bars(
                offer, 'H1', midnight, utc_now)[-1].date
            if lowest_hour > midnight:
                lowest_min = self._get_bars(
                    offer, 'm1', midnight,
                    lowest_hour+timedelta(minutes=60)
                )[-1].date
            else:
                lowest_min = utc_now
            return lowest_min
        except IndexError:
            return utc_now

    def current_tradingweek(self):
        """Takes the latest daily bar date time to setup
        initial system dates."""
        init_dt = self.get_current_bar('GBP/USD', 'D1')
        if init_dt.weekday() == 6: # Its Sunday
            wk_str = init_dt
        else:
            wk_str = init_dt - timedelta(days=init_dt.weekday()+1)
        wk_end = wk_str + timedelta(days=5)
        return wk_str, wk_end

    def get_current_bar(self, offer, time_frame):
        """Gets the current bar date time"""
        bars = self._get_bars(
            offer, time_frame, datetime.utcnow()-timedelta(days=14),
            datetime.utcnow()
        )
        return bars[0].date

    def dtype(self):
        return np.dtype(
            [('date', '<M8[us]'), ('askopen', '<f8'),
             ('askhigh', '<f8'), ('asklow', '<f8'),
             ('askclose', '<f8'), ('bidopen', '<f8'),
             ('bidhigh', '<f8'), ('bidlow', '<f8'),
             ('bidclose', '<f8'), ('volume', '<i8')]
        )

    def _get_bars(self, offer, time_frame, dtfm, dtto):
        """
        TODO Doc string.....
        """
        return self._session.get_historical_prices(
            offer.encode(),
            to_ole(dtfm),
            to_ole(dtto),
            time_frame.encode()
        )

    def _bars(self, offer, time_frame, dtfm, dtto):
        """
        Gets price data from FXCM, converts to a numpy array
        and performs a basic integrity check
        """
        fxdata = self._get_bars(offer, time_frame, dtfm, dtto)
        a = np.array(
            [v.__getinitargs__() for v in fxdata], dtype=self.dtype()
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
        TODO Doc string.....
        """
        if isinstance(dtfm, str):
            dtfm = datetime.strptime(dtfm, '%Y-%m-%d %H:%M')
        if isinstance(dtto, str):
            dtto = datetime.strptime(dtto, '%Y-%m-%d %H:%M')
        f = to_ole
        if dtfm < dtto:
            while (f(dtto) - f(dtfm)) > 0.0001:
                try:
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
                    if len(data) == 1:
                        break
                except RuntimeError:
                    # Catch: Session timeouts etc from the C++
                    pass


class FXCMTrading(AbstractFXCMBroker):
    """
    The FXCMTrading object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """
    def __init__(self):
        self._session = self._trading()

    def enter_position(self):
        """
        TODO Doc string.....
        """
        pass
        
    def liqudate_position(self):
        """
        TODO Doc string.....
        """
        pass
        
    def liqudate_all_positions(self):
        """
        TODO Doc string.....
        """
        pass
        
    def enter_stop_loss(self):
        """
        TODO Doc string.....
        """
        pass
        
    def enter_limit_order(self):
        """
        TODO Doc string.....
        """
        pass
