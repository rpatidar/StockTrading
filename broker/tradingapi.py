class TradingAPI(object):
    def __init__(self, credential, configuration, trade_runner):
        # self.credential = credential
        self.trade_runner = self._get_trading_service(
            credential, configuration, trade_runner
        )

    def _get_trading_service(self, credential, configuration, trade_runner):
        return trade_runner(credential, configuration)

    def on_tick_update(self, callback_function):
        self.trade_runner.on_tick_update(callback_function)

    def on_day_closure(self, callback_function):
        self.trade_runner.on_day_closure(callback_function)

    def place_order(self, order_details):
        pass

    def run(self):
        self.trade_runner.init_listening()
        pass

    def shutdown(self):
        self.trade_runner.shutdown()
