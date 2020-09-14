from zerodha.zeroda_base import ZerodhaServiceBase

from concurrent.futures import ThreadPoolExecutor

class ZerodhaServiceIntraDay(ZerodhaServiceBase):
    def __init__(self, credential, configuration):
        super(ZerodhaServiceIntraDay, self).__init__(credential, configuration)
        self.thread_pool_strategy = ThreadPoolExecutor(10)

    def init_listening(self):

        # Call from constructor
        self._get_instrumentnts()

        # TODO: start a back thread to replay the 1 minute data with date
        back_testing_config = self.configuration['back_testing_config']
        stocks_configs = back_testing_config['stocks_config']
        trades = []
        for stock, stock_config in stocks_configs.items():
            instrument_data = self._instrument_row(self.instruments, stock)
            if instrument_data == None:
                continue
            instrument_token = instrument_data['instrument_token']
            trades.append(self.thread_pool_strategy.submit(self.execute_strategy_single_datapoint, instrument_token, stock, stock_config));
            #self.execute_strategy_single_datapoint(instrument_token, stock, stock_config)
        for t in trades:
            t.result()
        pass

    def execute_strategy_single_datapoint(self, instrument_token, stock, stock_config):
        print("\n ==================================\nBacktesting now: {0} ".format(stock))
        from_date = stock_config['from']
        to_date = stock_config['to']
        trading_data = self._get_trading_data(stock, instrument_token, from_date, to_date)
        previous_date = None
        for trade_data in trading_data:
            # ohlc = copy.deepcopy(ohlcp)
            if previous_date != None and previous_date.date() != trade_data['date'].date():
                self.close_day(previous_date, instrument_token)
                previous_date = trade_data['date']
            previous_date = trade_data['date']
            decorated_trading_data = {'instrument_token': instrument_token, 'ohlc': trade_data}
            timestamp = trade_data['date']
            self._update_tick_data([decorated_trading_data], timestamp)
        if previous_date != None:
            self.close_day(previous_date, instrument_token)
