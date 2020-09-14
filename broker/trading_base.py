from broker.indan_stock import NSETradingSystem


class TradingService:
    def __init__(self, credential, configuration):
        self.credential = credential
        self.configuration = configuration
        print("Creating a trading service")
        # Find some way to keep the data immutable with the parent callback
        self.callbacks = []
        self.day_closure_callbacks = []

        pass

    def on_tick_update(self, callback_function):
        # if NSETradingSystem.isAfterMarketHours():
        #     print("After the Trading hours, Ignoring the tick")
        # else:
        self.callbacks.append(callback_function)

    def on_day_closure(self, callback_function):
        self.day_closure_callbacks.append(callback_function)

    def init_listening(self):
        pass

    def _update_tick_data(self, tick_data, timestamp):
        for callback in self.callbacks:
            callback(tick_data, timestamp)

    def close_day(self, date, instrument_token):
        for callback in self.day_closure_callbacks:
            callback(date, instrument_token)
