import logging


class ShadowTradingService(object):
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
