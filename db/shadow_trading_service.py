import logging

from broker.zerodha.zeroda_base import ZerodhaServiceBase


class ShadowTradingService(ZerodhaServiceBase):
    def __init__(self, credential):
        # Ignore the credentail as its hard coded inside as of now.
        super(ShadowTradingService, self).__init__(credential, None)

    def enter(self, type, instrument_token, date, price, strategy):
        logging.info(
            "+Got Enter for {0} at date {1}".format(instrument_token, str(date))
        )
        pass

    def exit(self, type, instrument_token, date, price, strategy):
        logging.info(
            "-Got Exit for {0} at date {1}".format(instrument_token, str(date))
        )
        pass
