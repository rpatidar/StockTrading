import datetime

from trendlinestrategy import TrendlineStrategy
from zerodha.zeroda_intraday_backtester import ZerodhaServiceIntraDay
from db import storage

"""
Trading System to Automate the Strategy execution in DB
1. It can listen to the tick data for a list of stock from the CSV File
2. It can insert the tick data into DB
3. It can execute the configured Strategy For specific stock
4. It can execute a default trading strategy

5. Risk management
6. Ordering Management - Can Resume the system from where it stopped.
7. Support the multiple trading platform

"""


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


class RiskManagement:
    def __init__(self):
        pass


#             self.balance = balance
#         def deduct(self):


class TradingSystem(object):

    def __init__(self, credential, configuration, tradeRunner, stratagies):
        self.stratagies = stratagies
        self.tradingAPI = TradingAPI(credential, configuration, tradeRunner)
        self.tradingAPI.on_tick_update(self.record_in_db)
        self.tradingAPI.on_tick_update(self.strategy_runner)
        self.tradingAPI.on_day_closure(self.day_closure)
        self.riskmanagement = RiskManagement()

    def run(self):
        self.tradingAPI.run()

    def __get_ohlc(self, ohlc1, ohlc2):
        ohlc_new = {}
        ohlc_new['low'] = min(ohlc1['low'], ohlc2['low'])
        ohlc_new['high'] = max(ohlc1['high'], ohlc2['high'])
        ohlc_new['open'] = ohlc1['open']
        ohlc_new['close'] = ohlc2['close']

        # ohlc_new['volume'] = ohlc1['volume'] + ohlc2['volume']
        return ohlc_new


    def day_closure(self, date):
        for strategy in self.stratagies:
            strategy.close_day(date)

    def summery(self):
        for strategy in self.stratagies:
            strategy.summary()

    def record_in_db(self, td, timestamp):
        # Recording data in DB[{'tradable': True, 'mode': 'quote', 'instrument_token': 5633, 'last_price': 1357.85, 'last_quantity': 25, 'average_price': 1346.6, 'volume': 713412, 'buy_quantity': 226, 'sell_quantity': 0, 'ohlc': {'open': 1333.0, 'high': 1361.8, 'low': 1326.65, 'close': 1338.65}, 'change': 1.4342808052888967}]
        tick_data = td[0]
        it = tick_data['instrument_token']
        ohlc = tick_data['ohlc']
        current_time = timestamp.replace(second=0, microsecond=0)
        storage.get_db().setdefault(it,{"1minute": {}, "5minute": {}})

        for agg_type in [1,5]:
            agg_key= str(agg_type) + "minute"
            agg_data = storage.get_db()[it][agg_key]
            last_agg_minute = (int(timestamp.minute/agg_type))*agg_type
            agg_datetime = timestamp.replace(minute=last_agg_minute, second=0, microsecond=0)

            if agg_datetime in agg_data:
                updated_agg = self.__get_ohlc(agg_data[agg_datetime], ohlc)
                agg_data[agg_datetime] = updated_agg
                updated_agg['date'] = agg_datetime
            else:
                agg_data[current_time] = ohlc

        #print("Recording data in DB" + str(tick_data))

    def strategy_runner(self, tick_data, timestamp):
        for strategy in self.stratagies:
            order_details = strategy.run(tick_data, self.riskmanagement, timestamp)
            if order_details != None:
                break
        pass

api_key = 'f6jdkd2t30tny1x8'
api_secret = 'eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo'
storage.init()
tradingSystem = TradingSystem({"api_key": api_key, "api_secret": api_secret}, {
    "back_testing_config": {"stocks_config": {"ZEEL": {"from": "2020-08-01", "to": "2020-08-31"}}}},
                              ZerodhaServiceIntraDay, [TrendlineStrategy()]) #
# tradingSystem = TradingSystem({"api_key": api_key, "api_secret": api_secret}, {
#     "back_testing_config": {"stocks_config": {"ZEEL": {"from": "2020-08-18", "to": "2020-09-04"}}}},
#                               ZerodhaServiceIntraDay, [TrendlineStrategy()]) #

tradingSystem.run()

input("Enter to exit")

tradingSystem.summery()