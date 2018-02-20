from ..base import AbstractBroker
from abc import ABCMeta
from forexconnect import (
    ForexConnectHistoryClient,
    ForexConnectOffersClient,
    ForexConnectTradingClient,
    set_log_level
)

set_log_level(9)



class AbstractFXCMBroker(AbstractBroker):
    """
    The AbstractFXCMBroker object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """

    __metaclass__ = ABCMeta

    def url(self):
        return 'http://www.fxcorporate.com/Hosts.jsp'

    def env(self):
        return 'real'

    def whoami(self):
        return 'fxcm'

    def supported_timeframes(self):
        return [
            'm1', 'm5', 'm15', 'm30', 'H1',
            'H2', 'H4', 'H8', 'D1', 'W1', 'M1'
        ]

    def is_connected(self):
        return self._session.is_connected()
        
    def _offers_table(self):
        return self._create_session(ForexConnectOffersClient)

    def _market_data(self):
        return self._create_session(ForexConnectHistoryClient)

    def _trading(self):
        return self._create_session(ForexConnectTradingClient)

    def _create_session(self, session_type):    
        import time
        rest = 0
        dir = '/home/nonroot/.fxcmcredentials'
        with open(dir) as f:
            credentials = f.readlines()
        user, passwd = credentials[0].strip().split(':') 
        while True:
            rest+=1
            try:
                session = session_type(
                    user.encode(), passwd.encode(),
                    self.env().encode(), self.url().encode()
                )
                if session.is_connected():
                    return session
            except RuntimeError as e:
                time.sleep(rest)

    def _logout_session(self):
        self._session.logout()
