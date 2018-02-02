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
        self.time_frames = self.br_handler.supported_time_frames
        self._subprocess_manager()

    def _setup_database(self, instruments):
        for instrument in instruments:
            # Setup each instrument
            self.db_handler.create(
                  instrument, self.time_frames
            )
        self.datebases = self.db_handler.databases

    def _start_subprocess(self, offers):
        selections = {}
        instruments = list(offers.keys())
        instruments.sort()
        for index, item in enumerate(instruments):
            selections[index] = item
            print(index, item)
        message = """

        .---..-..-.
        | |-  >  < 
        `-'  '-'`-`
                   
        .---..----..-.   .-.   .---..---..---.
        | |  | || || |__ | |__ | |- | |  `| |'
        `---'`----'`----'`----'`---'`---' `-' 


        There are lots of offers to track at FXCM.
        Its best to only track what you intend to trade.
        Lots of connections will cause login timeouts and 
        high RAM usage : (

        Select 10 instruments you want to track


        Enter the index number separating by comma ,
        1,3,30,20,44,2

        """
        print(message)
        user_selection = input("Input >>> : : ").split(',')
        results = list(map(int, user_selection))
        print(": : : : : : : : : : : : : : : : : : : : :")
        print(": : : : : : : : : : : : : : : : : : : : :")
        for index in results:
            instrument = selections[index]
            if instrument not in self.subscriptions:
                broker = self.broker
                s = subprocess.Popen(
                    ['python3', 'collection.py', broker, instrument]
                )
                self.subscriptions[instrument] = s
                time.sleep(20) # Watch out for login timeouts

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
