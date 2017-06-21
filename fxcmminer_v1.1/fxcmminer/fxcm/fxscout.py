import re
from collections import defaultdict
from time import sleep
from event import OfferEvent
from base import AbstractFxcmScout
from database.base import DatabaseManager
from xmlparsers.catalogparser import XMLCatalogue


class Scout(AbstractFxcmScout):
    """
    Responsiable for poling all tradable offers from FXCM.
    http://pricehistory.fxcorporate.com/pricearchive/catalog.xml
    """

    def __init__(self, hist_queue, time_frames):
        self.hist_queue = hist_queue
        self.tframes = time_frames
        self.current_databases = DatabaseManager().get_databases()

    def _new_offers(self, available_fxoffers):
        """
        """
        scouts_fxoffers = []
        catalog = self.return_catalog()
        for offer in catalog:
            if offer in available_fxoffers:
                scouts_fxoffers.append(offer)

        self._store_offers(scouts_fxoffers)
        self._initialise_offers()

    def _scouting(self):
        """
        Continuiosly poles FXCM for avaiable offers to trade and
        compares the lenght of two lists, which are the 
        available fxoffers list direct from FXCM and 
        the tracked fxoffers list created by Scout class. If the
        a new offer comes available, the FXCM cataloge is refreshed.
        """
        print("[:)] Scout Started..")
        fxc = self._fx_connection()
        self.tracked_offers = []
        while True:
            available_fxoffers = self._get_offers(fxc)
            #available_fxoffers = ['GBP/USD']
            if len(available_fxoffers) > len(self.tracked_offers):
                self.update_catalog()
                self._new_offers(available_fxoffers)
            sleep(1)

    def _initialise_offers(self):
        """
        Iterates through the tracked offers and compares the list
        to the current databases then, creates each database as
        nessacerry. A group of offers are then placed  into the
        historical data collection queue.
        """
        fxoffers = []
        iters = 0
        for xoffer in self.scout_offers:
            iters += 1
            if xoffer not in self.tracked_offers:
                print("[^^] SCOUT | Tracked  : %s" % xoffer)
                self.tracked_offers.append(xoffer)
                fxoffers.append(xoffer)
                offer = re.sub('[^A-Za-z0-9]+','',xoffer)
                if (offer not in self.current_databases and
                    xoffer in self.tracked_offers
                ):
                    DatabaseManager().database_creation(offer, self.tframes)
                    self.current_databases = DatabaseManager(
                        ).get_databases()
                # This is set to 10 to stop responce timeout errors
                # with FXCM servers.
                if len(fxoffers) == 10 or iters == len(self.scout_offers):
                    self.hist_queue.put(OfferEvent(fxoffers, self.tframes))
                    fxoffers = []

    def run(self):
        self._scouting()
