import logging
import threading
import datetime
import json
from kiteconnect import KiteTicker
from broker.indan_stock import NINE_AM, NINE_FIFTEEN_AM, THREE_FORTY_PM, FOUR_PM
from broker.trading_base import TradingService

from broker.zerodha.zeroda_base import ZerodhaServiceBase
import queue,threading

class ZerodhaServiceOnline(ZerodhaServiceBase):
    """
        Realtime tick provider data
    """
    def __init__(self, credential, configuration):
        super(ZerodhaServiceOnline, self).__init__(credential, configuration)
        self.intresting_stocks = self.configuration['stocks_to_subscribe']
        self.intresting_stocks_full_mode = self.configuration['stocks_in_fullmode']
        self.__setup()
        #Start warmup exercise in parallel
        self.warmup_tracker = {}
        threading.Thread(target=self._preload_historical_data).start()
        # initialize the thread to handle the tick data in a seperate
        self.q = queue.Queue()
        self.queue_handler = threading.Thread(target=self.queue_based_tick_handler, args=());
        self.queue_handler.start()
        self.tick_file_handler = open("./tmp/" + datetime.datetime.now().strftime("%Y-%m-%d") + ".tick", 'a+')

    def __setup(self):
        self.kws = KiteTicker(self.api_key, self.access_token)
        # Assign the callbacks.
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.on_reconnect = self.on_reconnect

    def on_ticks(self, ws, ticks):
        """Outside business range update ticks should be ignored"""
        if not (NINE_FIFTEEN_AM < datetime.datetime.now() < THREE_FORTY_PM):
            return

        if datetime.datetime.now() > THREE_FORTY_PM :
            self.tick_file_handler.close()

        # Callback to receive ticks.
        self.tick_file_handler.write(str(datetime.datetime.now()) + "\t" + json.dumps(ticks) + "\n")
        logging.debug("Received ticks")
        # Little approximation on time.
        #t = threading.Thread(target=self._update_tick_data, args=(ticks, datetime.datetime.date.now()))
        self.q.put((ticks, datetime.datetime.now()))
        #self._update_tick_data(ticks, datetime.datetime.now())

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

    # Callback when reconnect is on progress
    def on_reconnect(self, ws, attempts_count):
        print("Reconnecting: {}".format(attempts_count))
        logging.info("Reconnecting: {}".format(attempts_count))

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
            self.warmup_tracker[instrument_data['instrument_token']] = True

        logging.info("Preloading the data Completed")

    def queue_based_tick_handler(self):
        while True:
            ticks, timestamp  = self.q.get(block=True)

            #Only use stocks whose current data is loaded in memory already
            filtered_ticks = []
            for t in ticks:
                if t['instrument_token'] in self.warmup_tracker:
                    filtered_ticks.append(t)

            self._update_tick_data(filtered_ticks, timestamp)

    def on_close(self, ws, code, reason):
        logging.error("Websocket Error Code: " +  str(code))
        logging.error("Reason: " +  str(reason))
        #Comment the code for debugging
        # if NINE_AM < datetime.datetime.now() < FOUR_PM:
        #     logging.info("Stopping the reconnect as outside of bussiness hours")
        #ws.stop()

        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        #
        #     logging.info("Retrying again.")
        #     self.init_listening()
        # else:
        #     logging.error("not retrying as market is closed")


    def init_listening(self):
        logging.info("About to Start Zeroda Connect")
        self.kws.connect(threaded=True)

    def _background_listener(self):
        # if self.kws.is_connected():
            # Connect in a asynchronous threads
        pass
