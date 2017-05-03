from collections import defaultdict
from event import OfferEvent
import forexconnect as fx
import settings as s
from time import sleep
import multiprocessing as mp
from bs4 import BeautifulSoup
import urllib2


class Scout(mp.Process):
    """
    Responsiable for poling all tradable offers from FXCM.
    Once offers have been discovered they are placed into the 
    queue for processing by the Database Manager.

    http://pricehistory.fxcorporate.com/pricearchive/catalog.xml
    """
    def __init__(self, events_queue):
        mp.Process.__init__(self)
        """Initialize varables"""
        self.events_queue = events_queue
        self.tframes = s.TIME_FRAMES
        self.XML_FILE = s.XML_FILE

    def _scouting(self):
        """
        Continuiosly poles FXCM for avaiable offers to trade.
        """
        url = "http://pricehistory.fxcorporate.com/pricearchive/catalog.xml"
        
        while True:
            try:
                fxc = fx.ForexConnectClient(s.FX_USER,
                                            s.FX_PASS,
                                            s.FX_ENVR,
                                            s.URL)
                if fxc.is_connected() == True:
                    break
            except RuntimeError:
                pass

        print("Scout started..")

        offers = []
        tracked = []
        fxo = []
        while True:
            fxo = [x for x in fxc.get_offers() if x not in fxo]
            if len(fxo) > len(offers):
                offers = []
                xml = urllib2.urlopen(url).read()
                with open(self.XML_FILE, 'wb') as f:
                    f.write(xml)
                with open(self.XML_FILE, 'r') as f:
                    soup = BeautifulSoup(f.read(), 'lxml-xml')
                    for symbol in soup.find_all('symbol'):
                        if symbol['price-stream'] == 'Default':
                            if symbol['name'] in fxo:
                                offers.append(symbol['name'])

                tracked = [x for x in offers if x not in tracked]

                self._reporting(tracked)

            # TODO : Remove offer from Live tracking

            sleep(0.1)

    def _reporting(self, tracked):
        """
        Reports the FXCM offers to the Database Manager.
        """
        #tracked = ['XAU/USD', 'XAG/USD', 'GBP/USD']
        for x in tracked:
            fxoffer = defaultdict(dict)
            fxoffer[x] = self.tframes
            if dict(fxoffer) != {}:
                self.events_queue.put(OfferEvent(dict(fxoffer)))
                print("[>>] Tracked : %s") % x
                sleep(20) # Slows the starting process

    def run(self):
        self._scouting()
