from database import DatabaseHandler
from broker import FXCMBrokerHandler

import subprocess
import time
import sys
import re

class MainAggregator(object):
    def __init__(self):
        """
        The MainAggregator class is just here to setup the initial
        databases and then start each subprocess.
        
        I'm going to change the name because its shit.
        
        Later updates will have database health monitoring or
        something, not sure, I am now just writing aimlessly because
        I don't know what else to put here.
        
        More fun in collection.py
        """
        self.broker = 'fxcm'
        self.db_handler = DatabaseHandler(self.broker)
        self.br_handler = FXCMBrokerHandler()
        self.subscriptions = {}
        self.datebases = self.db_handler.get_databases()
        self.time_frames = self.br_handler.supported_time_frames
        self._subscriptions_manager()

    def _setup_database(self, instruments):
        for instrument in instruments:
            if instrument.replace('/','') not in self.datebases:
                # Setup each instrument
                self.db_handler.create(
                      instrument, self.time_frames
                )
            self.datebases = self.db_handler.get_databases()

    def _start_subprocess(self, instruments):
        # There are lots of offers to track at FXCM.
        # Its best to only track what you intend to trade.
        # Lots of connections will cause login timeouts and 
        # high RAM usage : ( 
        # Some defaults below have been set.
        instruments = ['EUR/USD', 'USD/JPY', 'GBP/USD',
                       'AUD/USD', 'USD/CHF', 'NZD/USD',
                       'USD/CAD', 'USDOLLAR', 'UK100']
        #instruments = ['EUR/USD']
        #instruments = ['GBP/USD','UK100']
        for i in instruments:
            if i not in self.subscriptions:
                broker = self.broker
                instrument = i
                s = subprocess.Popen(
                    ['python3', 'collection.py', broker, instrument]
                )
                self.subscriptions[i] = s
                time.sleep(5) # Watch out for login timeouts

    def _subprocess_manager(self):
        instruments = self.br_handler.get_offers()
        self._setup_database(instruments)
        self._start_subprocess(instruments)
        self.br_handler.session.logout()
        try:
            while True:
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
