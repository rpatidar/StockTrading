import logging
import threading
import datetime
from kiteconnect import KiteTicker

from broker.trading_base import TradingService

from zerodha.zeroda_base import ZerodhaServiceBase


class ZerodhaServiceOnline(ZerodhaServiceBase):
    def __init__(self, credential, configuration):
        super(ZerodhaServiceOnline, self).__init__(credential, configuration)
        self.intresting_stocks = self.configuration['stocks_to_subscribe']
        self.intresting_stocks_full_mode = self.configuration['stocks_in_fullmode']
        self.__setup()

        # initialize the thread

    def __setup(self):
        self.kws = KiteTicker(self.api_key, self.access_token)
        # Assign the callbacks.
        self.kws.on_ticks = self.__on_ticks
        self.kws.on_connect = self.__on_connect
        self.kws.on_close = self.__on_close

    def __on_ticks(self, ws, ticks):
        # Callback to receive ticks.
        logging.debug("Ticks: {}".format(ticks))
        # Little approximation on time.
        self._update_tick_data(ticks, datetime.datetime.date.now())

    def __on_connect(self, ws, response):
        # Callback on successful connect.
        # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
        # [738561, 5633]

        ws.subscribe(self.intresting_stocks)
        # Set RELIANCE to tick in `full` mode.
        # [738561]
        ws.set_mode(ws.MODE_FULL, self.intresting_stocks_full_mode)

    def _preload_historical_data(self):
        """
        This is not the effective implementation, as of now blindly pre loading 1 week of data in memory.
        :return:
        """
        from datetime import datetime, timedelta
        todays_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        start_date = todays_date - timedelta(days=7)
        end_date = todays_date

        for stock in self.intresting_stocks:
            instrument_data = self._instrument_row(self.instruments, stock)
            if instrument_data == None:
                continue
            self.execute_strategy_single_datapoint(instrument_data['instrument_token'], stock,
                                                   {"from": start_date, "to": end_date}, backfill=True)

    def __on_close(self, ws, code, reason):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        ws.stop()

    def init_listening(self):
        logging.info("About to Start Zeroda Connect")
        self.kws.connect()

        # t = threading.Thread(target=self._background_listener)
        # t.start()
        # logging.info("Started the Zeroda Connect")

    def _background_listener(self):
        if self.kws.is_connected():
            # Connect in a asynchronous threads
            self.kws.connect()
