import logging
import sys
import pandas
from messenger.tele_messenger import send_message
from broker.zerodha.zeroda_base import ZerodhaServiceBase


class ZerodhaLiveTradingService(ZerodhaServiceBase):
    """
    Helper utitlity to place the live orders in Zerodha
    """

    def __init__(self, credential):
        # Ignore the credentail as its hard coded inside as of now.
        super(ZerodhaLiveTradingService, self).__init__(credential, None)
        self.margin_info = pandas.read_csv(
            "resource/zeroda_margin_stocks.csv", index_col="script"
        )

        self.quantity_tracker = {}
        self.ongoing_trades = 0

    def enter(self, type, instrument_token, date, price, strategy):
        symbol, exchange = self.get_symbol_and_exchange(instrument_token)
        if self.ongoing_trades > 10:
            logging.info("Too many trades, not taking any trades for now")
            return

        if not symbol in self.margin_info.index:
            logging.info("Can't BUY trade with margin for the Stock {}".format(symbol))
            return

        # This logic should be updated by checking the actual amount and the leverage we can have self.margin_info[symbol]['leverage_margin']
        self.quantity_tracker[symbol] = (
            int(5000 / price) if price < 5000 and self.ongoing_trades < 5 else 1
        )

        logging.info(
            "+Got Enter for {0} at date {1}".format(instrument_token, str(date))
        )

        send_message(
            "-Got Enter for {0} at date {2} Price={1}".format(symbol, price, str(date))
        )

        try:
            #TODO: Try placing a limit order instead of market order
            #Backtest with last 1 year of data to see if its profimaking idea.
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=exchange,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=self.quantity_tracker[symbol],
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=self.kite.PRODUCT_MIS,
                variety=self.kite.VARIETY_REGULAR,
            )
            self.ongoing_trades = self.ongoing_trades + 1
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
        symbol, exchange = self.get_symbol_and_exchange(instrument_token)

        if not symbol in self.margin_info.index:
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
                quantity=self.quantity_tracker[symbol],
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
