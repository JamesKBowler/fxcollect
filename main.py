from database import DatabaseHandler
from broker import FXCMBrokerHandler

import subprocess
import time
import sys
import re


class MainAggregator(object):
    def __init__(self):
        self.broker = 'fxcm'
        self.db_handler = DatabaseHandler(self.broker)
        self.br_handler = FXCMBrokerHandler()
        self.subscriptions = {}
        self.datebases = self.db_handler.get_databases()
        self.time_frames = self.br_handler.supported_time_frames
        self._subscriptions_manager()

    def _setup_database(self, instruments):
        for instrument in instruments:
            # Setup each instrument
            self.db_handler.create(
                  instrument, self.time_frames
            )
            self.datebases = self.db_handler.get_databases()

    def _check_subscriptions(self, instruments):
        # There are lots of offers to track at FXCM.
        # Its best to only track what you intend to trade.
        # Lots of connections will cause login timeouts and 
        # high RAM useage : ( 
        # Some defaults below have been set.
        instruments = ['EUR/USD', 'USD/JPY', 'GBP/USD',
                       'AUD/USD', 'USD/CHF', 'NZD/USD'
                       'USD/CAD', 'USDOLLAR', 'UK100']
        for i in instruments:
            if i not in self.subscriptions:
                broker = self.broker
                instrument = i
                s = subprocess.Popen(
                    ['python3', 'collection.py', broker, instrument]
                )
                self.subscriptions[i] = s
                time.sleep(5) # Watch out for login timeouts

    def _subscriptions_manager(self):
        try:
            connected = False
            while True:
                if not self.br_handler._session_status():
                    self.br_handler._login()
                instruments = self.br_handler._get_instruments()
                self._setup_database(instruments)
                self._check_subscriptions(instruments)
                time.sleep(60)
        except KeyboardInterrupt:
            self._kill()
            
    def _kill(self):
        print('Kill Command sent to all SubProcesses')
        for s in self.subscriptions:
            self.subscriptions[s].kill()
        sys.exit(0)

print("Starting Collection, press CTRL+C to stop")
MainAggregator()