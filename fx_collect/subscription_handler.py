from termcolor import cprint
from .subscriptions import Subscriptions


class SubscriptionHandler(object):
    def __init__(
        self, events_queue, init_offers, init_signals,
        offer_broker, price_broker,
        database_handler
    ):
        self.events_queue = events_queue
        self.offer_broker = offer_broker
        self.price_broker = price_broker
        self.database_handler = database_handler
        self.subscriptions = Subscriptions(
            init_offers,
            init_signals,
            offer_broker,
            price_broker,
            database_handler
        )

    def _place_events_onto_queue(self, event_list):
        for event in event_list:
            self.events_queue.put(event)

    def check_subscriptions_jobs(self):
        if self.subscriptions.jobs:
            self._place_events_onto_queue(
                self.subscriptions.jobs)
            self.subscriptions.jobs = []

    def on_signal(self, event):
        cprint(event, 'yellow')
        self.subscriptions.record_signal(
            event.finished_bar,
            event.current_bar,
            event.next_bar,
            event.timeframe
        )

    def on_response(self, event):
        cprint(event, 'red')
        jobno = event.jobno
        offer = event.offer
        timeframe = event.timeframe
        self.subscriptions.response(jobno, offer, timeframe)
        self.check_subscriptions_jobs()

    def on_status(self):
        self.subscriptions.update_status()
        self.subscriptions.check_subscription()
        self.check_subscriptions_jobs()