from ..base import AbstractBroker
from abc import ABCMeta
from forexconnect import (
    ForexConnectHistoryClient,
    ForexConnectOffersClient,
    ForexConnectTradingClient,
    set_log_level
)
from traceback import print_exc
from ...settings import FXCM_CREDENTIALS, FXCM_CREDENTIALS_FILE

set_log_level(9)



class AbstractFXCMBroker(AbstractBroker):
    """
    The AbstractFXCMBroker object is designed to interact directly
    with FXCM using the python-forexconnect API.
    """

    __metaclass__ = ABCMeta

    def url(self):
        return 'http://www.fxcorporate.com/Hosts.jsp'

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
        if FXCM_CREDENTIALS:
            credentials = FXCM_CREDENTIALS
        else:
            if FXCM_CREDENTIALS_FILE:
                dir = FXCM_CREDENTIALS_FILE
                with open(dir) as f:
                    credentials = f.readlines()
                    credentials = credentials[0]
            else:
                raise (Exception("No FXCM credentials found. Modify settings.py before running the application."))
                
        fxcm_env, user, passwd = credentials.strip().split(':') 
        while True:
            if rest<60: rest+=1
            try:
                session = session_type(
                    user.encode(), passwd.encode(),
                    fxcm_env.encode(), self.url().encode()
                )
                if session.is_connected():
                    return session
            except RuntimeError as e:
                print_exc()
                time.sleep(rest)

    def _logout_session(self):
        self._session.logout()
