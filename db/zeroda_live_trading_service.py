import logging
import sys
import pandas
from messenger.tele_messenger import send_message
from broker.zerodha.zeroda_base import ZerodhaServiceBase


class ZerodhaLiveTradingService(ZerodhaServiceBase):
    def __init__(self, credential):
        # Ignore the credentail as its hard coded inside as of now.
        super(ZerodhaLiveTradingService, self).__init__(credential, None)
        self.margin_info = pandas.read_csv(
            "resource/zeroda_margin_stocks.csv", index_col="script"
        )

    def enter(self, type, instrument_token, date, price, strategy):
        symbol, exchange = self._get_symbol_and_exchange(instrument_token)

        if not symbol in self.margin_info:
            logging.info("Can't BUY trade with margin for the Stock {}".format(symbol))
            return

        logging.info(
            "+Got Enter for {0} at date {1}".format(instrument_token, str(date))
        )

        send_message(
            "-Got Enter for {0} at date {2} Price={1}".format(symbol, price, str(date))
        )

        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=exchange,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=1,
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=self.kite.PRODUCT_MIS,
                variety=self.kite.VARIETY_REGULAR,
            )
            logging.info("Buy Order placed. ID is: {}".format(order_id))
        except:
            e = sys.exc_info()
            logging.info(
                "Error while placing the BUY Order for {0}".format(symbol), exc_info=e
            )
            send_message(
                "Error while placing the BUY Order for {0}\n with Exception : ".format(
                    symbol, str(e)
                )
            )

    def exit(self, type, instrument_token, date, price, strategy):
        symbol, exchange = self._get_symbol_and_exchange(instrument_token)

        if not symbol in self.margin_info:
            logging.info("Can't SEL trade with margin for the Stock {}".format(symbol))
            return

        logging.info(
            "-Got Exit for {0} at date {1}".format(instrument_token, str(date))
        )

        send_message(
            "-Got Exit for {0} at date {2} Price={1}".format(symbol, price, str(date))
        )
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=exchange,
                transaction_type=self.kite.TRANSACTION_TYPE_SELL,
                quantity=1,
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=self.kite.PRODUCT_MIS,
                variety=self.kite.VARIETY_REGULAR,
            )
            logging.info("Sell Order placed. ID is: {}".format(order_id))
        except:
            e = sys.exc_info()
            logging.info(
                "Error while placing the SELL Order for {0}".format(symbol), exc_info=e
            )
            send_message(
                "Error while placing the SELL Order for {0}\n with Exception : ".format(
                    symbol, str(e)
                )
            )
