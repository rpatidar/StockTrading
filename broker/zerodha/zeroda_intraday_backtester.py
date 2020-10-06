from zerodha.zeroda_base import ZerodhaServiceBase

from concurrent.futures import ThreadPoolExecutor


class ZerodhaServiceIntraDay(ZerodhaServiceBase):
    def __init__(self, credential, configuration):
        super(ZerodhaServiceIntraDay, self).__init__(credential, configuration)
        self.thread_pool_strategy = ThreadPoolExecutor(1)

    def init_listening(self):

        # TODO: start a back thread to replay the 1 minute data with date
        back_testing_config = self.configuration['back_testing_config']
        stocks_configs = back_testing_config['stocks_config']
        trades = []
        for stock, stock_config in stocks_configs.items():
            instrument_data = self._instrument_row(self.instruments, stock)
            if instrument_data == None:
                continue
            instrument_token = instrument_data['instrument_token']
            # trades.append(self.thread_pool_strategy.submit(self.execute_strategy_single_datapoint, instrument_token, stock, stock_config));
            self.execute_strategy_single_datapoint(instrument_token, stock, stock_config)
        for t in trades:
            t.result()
        pass
