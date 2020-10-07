import logging
from kiteconnect import KiteTicker

logging.basicConfig(level=logging.DEBUG)

import os, datetime, pickle

class TestClass:
    def __init__(self):
        api_key = 'f6jdkd2t30tny1x8'
        api_secret = 'eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo'
        session_data = pickle.load(open("./tmp/session_file", "rb"))
        self.kws = KiteTicker(api_key, session_data['token'])
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close

    def on_ticks(self, ws, ticks):
        # Callback to receive ticks.
        logging.debug("Ticks: {}".format(ticks))

    def on_connect(self, ws, response):
        # Callback on successful connect.
        # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
        ws.subscribe([738561, 5633])

        # Set RELIANCE to tick in `full` mode.
        ws.set_mode(ws.MODE_FULL, [738561])

    def on_close(self, ws, code, reason):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        ws.stop()

    def start(self):
        self.kws.connect()

# Assign the callbacks.

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
t = TestClass()
t.start()