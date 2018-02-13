from fx_collect.session import CollectionSession
from queue import Queue

# offers = [
    # 'HKG33', 'EUR/SEK', 'CAD/CHF', 'AUS200', 'USD/NOK', 'EUSTX50', 'USD/CAD', 'CHF/JPY', 'EUR/AUD',
    # 'GBP/CAD', 'EUR/USD', 'GBP/CHF', 'USOil', 'NZD/CAD', 'USDOLLAR', 'EUR/NZD',
    # 'US30', 'Copper', 'Bund', 'GBP/USD', 'ESP35', 'EUR/CHF', 'USD/ZAR', 'USD/SEK', 'EUR/NOK',
    # 'GBP/JPY', 'GER30', 'SPX500', 'NZD/USD', 'XAU/USD', 'AUD/CAD', 'USD/HKD', 'UKOil', 'TRY/JPY',
    # 'USD/CNH', 'GBP/AUD', 'USD/CHF', 'CAD/JPY', 'XAG/USD', 'AUD/JPY', 'AUD/CHF', 'EUR/JPY',
    # 'UK100', 'USD/TRY', 'EUR/TRY', 'NZD/CHF', 'EUR/CAD', 'AUD/USD', 'NAS100', 'FRA40', 'GBP/NZD',
    # 'USD/MXN', 'EUR/GBP', 'ZAR/JPY', 'AUD/NZD', 'NZD/JPY', 'JPN225', 'USD/JPY', 'NGAS'
# ]
config = None
offers = ['GBP/USD', 'EUR/SEK', 'AUS200', 'EUSTX50', 'USD/CAD', 'HKG33', 'UK100']
events_queue = Queue()
collect_session = CollectionSession(
    config, offers, events_queue
)
collect_session.start_collection()
