import logging
import threading
import datetime
from kiteconnect import KiteTicker

from broker.trading_base import TradingService


class ZerodhaServiceOnline(TradingService):
    def __init__(self, credential, configuration):
        super(ZerodhaServiceOnline, self).__init__()
        self.configuration = configuration
        self._login(credential)
        self.__setup()
        # initialize the thread

    def __setup(self):
        self.kws = KiteTicker(self.api_key, self.access_token)
        # Assign the callbacks.
        self.kws.on_ticks = self.__on_ticks
        self.kws.on_connect = self.__on_connect
        self.kws.on_close = self.__on_close

    def f(self, ws, ticks):
        # Callback to receive ticks.
        logging.debug("Ticks: {}".format(ticks))
        # Little approximation on time.
        self._update_tick_data(ticks, datetime.datetime.date.now())

    def __on_connect(self, ws, response):
        # Callback on successful connect.
        # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
        # [738561, 5633]
        ws.subscribe(self.configuration['stocks_to_subscribe'])
        # Set RELIANCE to tick in `full` mode.
        # [738561]
        ws.set_mode(ws.MODE_FULL, self.configuration['stocks_in_fullmode'])

    def __on_close(self, ws, code, reason):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        ws.stop()

    def init_listening(self):
        logging.info("About to Start Zeroda Connect")
        self.kws.connect()

        t = threading.Thread(target=self._background_listener)
        t.start()
        logging.info("Started the Zeroda Connect")
        # self._background_listener()

    def _background_listener(self):
        pass
        # Run Kite  in background
        # print ("Running the background function, size of callbacks" + str(len(self.callbacks)))
