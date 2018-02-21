from fx_collect.collect_session import CollectionSession
from queue import Queue

# Try with just a few a first : )
offers = ['Copper' , 'GBP/USD', 'EUR/SEK', 'AUS200', 'EUSTX50', 'USD/CAD', 'HKG33', 'UK100']

# If offers is None, all offers will be collected.
# offers = None
events_queue = Queue()
collect_session = CollectionSession(
    events_queue, offers
)
collect_session.start_collection()
