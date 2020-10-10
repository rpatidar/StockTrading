import logging
import threading
import datetime
from kiteconnect import KiteTicker
from broker.indan_stock import NINE_AM, FOUR_PM
from broker.trading_base import TradingService

from broker.zerodha.zeroda_base import ZerodhaServiceBase

class ZerodhaServiceOnline(ZerodhaServiceBase):
    """
        Realtime tick provider data
    """
    def __init__(self, credential, configuration):
        super(ZerodhaServiceOnline, self).__init__(credential, configuration)
        self.intresting_stocks = self.configuration['stocks_to_subscribe']
        self.intresting_stocks_full_mode = self.configuration['stocks_in_fullmode']
        self.__setup()
        self._preload_historical_data()
        # initialize the thread

    def __setup(self):
        self.kws = KiteTicker(self.api_key, self.access_token)
        # Assign the callbacks.
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close

    def on_ticks(self, ws, ticks):
        """Outside business range update ticks should be ignored"""
        if not (NINE_AM < datetime.datetime.now() < FOUR_PM):
            return

        # Callback to receive ticks.
        logging.debug("Ticks: {}".format(ticks))
        # Little approximation on time.

        #t = threading.Thread(target=self._update_tick_data, args=(ticks, datetime.datetime.date.now()))
        self._update_tick_data(ticks, datetime.datetime.now())

    def on_connect(self, ws, response):
        # Callback on successful connect.
        # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
        # [738561, 5633]
        instrument_ids = []
        for stock in self.intresting_stocks:
            instrument_data = self._instrument_row(self.instruments, stock)
            if instrument_data:
                instrument_ids.append(instrument_data['instrument_token'])
            else:
                logging.error("Not able to find the stock:" + stock)
        logging.info("Subscribing :" + str(instrument_ids))
        ws.subscribe(instrument_ids)
        # Set RELIANCE to tick in `full` mode.
        # [738561]
        # ws.set_mode(ws.MODE_FULL, self.intresting_stocks_full_mode)


    def _preload_historical_data(self):
        """
        This is not the effective implementation, as of now blindly pre loading 1 week of data in memory.
        :return:
        # """
        logging.info("Preloading the data for old dates")
        from datetime import datetime, timedelta
        todays_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        start_date = todays_date - timedelta(days=7)
        end_date = todays_date

        for stock in self.intresting_stocks:
            instrument_data = self._instrument_row(self.instruments, stock)
            if instrument_data == None:
                continue
            self.execute_strategy_single_stock_historical(instrument_data['instrument_token'], stock,
                                                   {"from": start_date, "to": datetime.now()}, backfill=True)

        logging.info("Preloading the data Completed")

    def on_close(self, ws, code, reason):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        logging.error("Websocket Error Code: " +  str(code))
        logging.error("Reason: " +  str(reason))
        ws.stop()

        if NINE_AM < datetime.datetime.now() < FOUR_PM:
            logging.info("Retrying again.")
            self.init_listening()
        else:
            logging.error("not retrying as market is closed")


    def init_listening(self):
        logging.info("About to Start Zeroda Connect")
        self.kws.connect(threaded=True)

    def _background_listener(self):
        # if self.kws.is_connected():
            # Connect in a asynchronous threads
        pass

