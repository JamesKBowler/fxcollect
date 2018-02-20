from .base import AbstractFXCMBroker
from .tools import (
    FXCMOffersTable,
    FXCMMarketData,
    FXCMTrading
)


class FXCMBroker(AbstractFXCMBroker):
    def __init__(
        self,
        offers_table=True,
        market_data=True,
        trading=True
    ):
        if offers_table:
            self.offers_table = FXCMOffersTable()
        if trading:
            self.trading = FXCMTrading()
        if market_data:
            self.market_data = FXCMMarketData()
