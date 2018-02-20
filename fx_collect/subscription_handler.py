from termcolor import cprint
from .subscriptions import Subscriptions
        
        
class SubscriptionHandler(object):
    def __init__(
        self, events_queue, init_offers, init_signals,
        broker, database_handler
    ):
        self.events_queue = events_queue
        self.broker = broker
        self.database_handler = database_handler
        self.fxsubscriptions = Subscriptions(
            init_offers,
            init_signals,
            broker.offers_table,
            broker.market_data,
            database_handler, events_queue
        )

    def on_signal(self, event):
        cprint(event, 'yellow')
        self.fxsubscriptions.signals[event.timeframe] = {
            'fin': event.finished_bar,
            'cur': event.current_bar,
            'nxt': event.next_bar,
        }

    def on_response(self, event):
        cprint(event, 'red')
        jobno = event.jobno
        offer = event.offer
        timeframe = event.timeframe
        self.fxsubscriptions.response(jobno, offer, timeframe)

    def on_status(self):
        self.fxsubscriptions.update_status()
        self.fxsubscriptions.check_subscription()