class TradingAPI(object):
    def __init__(self, credential, configuration, tradeRunner):
        # self.credential = credential
        self.tradeRunner = self._get_trading_service(credential, configuration, tradeRunner)

    def _get_trading_service(self, credential, configuration, tradeRunner):
        return tradeRunner(credential, configuration)

    def on_tick_update(self, callback_function):
        self.tradeRunner.on_tick_update(callback_function)

    def on_day_closure(self, callback_function):
        self.tradeRunner.on_day_closure(callback_function)

    def place_order(self, order_details):
        pass

    def run(self):
        self.tradeRunner.init_listening()
        pass

    def shutdown(self):
        self.tradeRunner.shutdown()
