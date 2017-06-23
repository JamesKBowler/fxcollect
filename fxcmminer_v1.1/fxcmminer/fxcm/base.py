from xmlparsers.catalogparser import XMLCatalogue
from database.base import DatabaseManager
from catalogdict.catalogdict import InstrumentDictCatalog
import forexconnect as fx
from settings import FX_USER, FX_PASS, FX_ENVR, URL, PICKLE
import pandas as pd
import pickle
pd.set_option('expand_frame_repr', False)

class AbstractFxcm(object):
    """
    """
    def _fx_connection(self):
        """
        Creates a session with FXCM.
        """
        while True:
            try:
                fxc = fx.ForexConnectClient(
                    FX_USER, FX_PASS, FX_ENVR, URL)
                if fxc.is_connected() == True:
                    break
            except RuntimeError:
                pass
        return fxc

    def get_data(self, fxc, instrument, fm_date, to_date, time_frame):
        """
        Calls FXCM for a given offer and time frame, collects data then
        return a Pandas pd.DataFrame.
        """
        values = fxc.get_historical_prices(
            str(instrument), fm_date, to_date, str(time_frame))
        data = [v.__getstate__()[0] for v in values]
        try:
            return pd.DataFrame.from_records(data, index = "date").round(6)
        except KeyError:
            return pd.DataFrame()

class AbstractFxcmScout(AbstractFxcm):
    """
    """
    def update_catalog(self):
        with open(PICKLE, 'wb') as onions:
            pickle.dump(XMLCatalogue().start_parser('Default'),
            onions, protocol=pickle.HIGHEST_PROTOCOL)

    def return_catalog(self):
        with open(PICKLE, 'rb') as h:
            catalog = pickle.load(h)
        return catalog    

    def _get_offers(self, fxc):
        available_fxoffers = [
            offer for offer in fxc.get_offers()
        ]
        return available_fxoffers

    def _store_offers(self, offers):
        self.scout_offers = [
            o for o in offers
        ]

class AbstractFxcmHistorical(AbstractFxcm):
    """
    """
    def _get_init_date(self, offer, time_frame):
        """
        """
        init_date = DatabaseManager().latest_dbdate(offer, time_frame)
        if init_date == None:
            catalog = AbstractFxcmScout().return_catalog()
            init_date = InstrumentDictCatalog(
                ).date_extract(offer, time_frame, catalog)
        return init_date

class AbstractFxcmLive(AbstractFxcm):
    """
    """
    def _get_init_date(self, offer, time_frame):
        """
        """
        return DatabaseManager().latest_dbdate(offer, time_frame)
