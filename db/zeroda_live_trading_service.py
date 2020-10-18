import logging

import telegram

from broker.zerodha.zeroda_base import ZerodhaServiceBase

b = telegram.bot.Bot("1370331323:AAHe9lBTseBxn5KvA8v2SQbGp8RGbLToa30")


class ZerodhaLiveTradingService(ZerodhaServiceBase):

    def __init__(self, credential):
        # Ignore the credentail as its hard coded inside as of now.
        super(ZerodhaLiveTradingService, self).__init__(credential, None)

    def enter(self, type, instrument_token, date, price, strategy):
        symbol, exchange = self._get_symbol_and_exchange(instrument_token)
        logging.info("+Got Enter for {0} at date {1}".format(instrument_token, str(date)))
        b.send_message(chat_id=-478351687, text="+Got Enter for {0} at date {1}".format(instrument_token, str(date)))

        order_id = self.kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                                    quantity=1,
                                    order_type=self.kite.ORDER_TYPE_MARKET,
                                    product=self.kite.PRODUCT_MIS,
                                    variety=self.kite.VARIETY_REGULAR)

        logging.info("Buy Order placed. ID is: {}".format(order_id))

    def exit(self, type, instrument_token, date, price, strategy):
        logging.info("-Got Exit for {0} at date {1}".format(instrument_token, str(date)))
        b.send_message(chat_id=-478351687, text="-Got Exit for {0} at date {1}".format(instrument_token, str(date)))

        symbol, exchange = self._get_symbol_and_exchange(instrument_token)
        order_id = self.kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=self.kite.TRANSACTION_TYPE_SELL,
                                    quantity=1,
                                    order_type=self.kite.ORDER_TYPE_MARKET,
                                    product=self.kite.PRODUCT_MIS,
                                    variety=self.kite.VARIETY_REGULAR)
        logging.info("Sell Order placed. ID is: {}".format(order_id))
