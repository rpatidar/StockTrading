import logging
from broker.zerodha.zeroda_base import ZerodhaServiceBase

class ZerodhaLiveTradingService(ZerodhaServiceBase):

    def __init__(self):
        # Ignore the credentail as its hard coded inside as of now.
        super(ZerodhaLiveTradingService, self).__init__({"api_key": "f6jdkd2t30tny1x8", "api_secret": "eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo"}, None)

    def enter(self, type, instrument_token, date, price, strategy):
        symbol, exchange = self._get_symbol_and_exchange(instrument_token)
        logging.info("+Got Enter for {0} at date {1}".format(instrument_token, str(date)))

        order_id = self.kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                                    quantity=1,
                                    order_type=self.kite.ORDER_TYPE_MARKET,
                                    product=self.kite.PRODUCT_NRML)

        logging.info("Order placed. ID is: {}".format(order_id))
        pass

    def exit(self, type, instrument_token, date, price, strategy):
        logging.info("-Got Exit for {0} at date {1}".format(instrument_token, str(date)))
        symbol, exchange = self._get_symbol_and_exchange(instrument_token)
        order_id = self.kite.place_order(tradingsymbol=symbol,
                                    exchange=exchange,
                                    transaction_type=self.kite.TRANSACTION_TYPE_SELL,
                                    quantity=1,
                                    order_type=self.kite.ORDER_TYPE_MARKET,
                                    product=self.kite.PRODUCT_NRML)
        pass
