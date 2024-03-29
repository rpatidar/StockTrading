from broker.tradingapi import TradingAPI
from db.storage import StorageHandler


class TradingSystem(object):
    def __init__(self, credential, configuration, trade_runner, stratagies):
        self.stratagies = stratagies
        self.tradingAPI = TradingAPI(credential, configuration, trade_runner)
        self.tradingAPI.on_tick_update(self.record_in_db)
        self.tradingAPI.on_tick_update(self.strategy_runner)
        self.tradingAPI.on_day_closure(self.day_closure)

    def run(self):
        self.tradingAPI.run()

    def __get_ohlc(self, ohlc1, ohlc2):
        ohlc_new = {}
        ohlc_new["low"] = min(ohlc1["low"], ohlc2["low"])
        ohlc_new["high"] = max(ohlc1["high"], ohlc2["high"])
        ohlc_new["open"] = ohlc1["open"]
        ohlc_new["close"] = ohlc2["close"]
        ohlc_new['volume'] = ohlc1['volume'] + ohlc2['volume']
        # ohlc_new['volume'] = ohlc1['volume'] + ohlc2['volume']
        return ohlc_new

    def day_closure(self, date, instrument_token, backfill=False, execution_info = None):
        for strategy in self.stratagies:
            strategy.close_day(date, instrument_token, backfill=backfill, execution_info=execution_info)

    def summery(self):
        for strategy in self.stratagies:
            strategy.summary()

    """
        TODO: 
        1) Store this data in some time series DB
        2) build capability to aggregate based on the #1 minute, #5 minute level
    """

    def record_in_db(self, ticks, timestamp, backfill=False):
        # Recording data in DB[{'tradable': True, 'mode': 'quote', 'instrument_token': 5633, 'last_price': 1357.85, 'last_quantity': 25, 'average_price': 1346.6, 'volume': 713412, 'buy_quantity': 226, 'sell_quantity': 0, 'ohlc': {'open': 1333.0, 'high': 1361.8, 'low': 1326.65, 'close': 1338.65}, 'change': 1.4342808052888967}]
        for tick_data in ticks:
            it = tick_data["instrument_token"]
            ohlc = tick_data["ohlc"]
            current_time = timestamp.replace(second=0, microsecond=0)
            sh = StorageHandler()
            sh.get_db().setdefault(it, {"1minute": {}, "5minute": {}})

            """ 1 Minute and 5 minute aggregation assuming the tick data is of any """
            for agg_type in [1]:
                agg_key = str(agg_type) + "minute"
                last_agg_minute = (int(timestamp.minute / agg_type)) * agg_type
                agg_datetime = timestamp.replace(
                    minute=last_agg_minute, second=0, microsecond=0
                )
                trading_date = timestamp.date()
                record = None
                inst_data = sh.get_db()[it][agg_key]
                # if inst_data is None:
                #     inst_data = []
                #     sh.get_db()[it][agg_key] = inst_data

                last_day_records = inst_data.get(trading_date)
                if last_day_records is None:
                    last_day_records = []
                    inst_data[trading_date] = last_day_records
                if len(last_day_records) > 0 and last_day_records[-1]['date'] == agg_datetime:
                    record = last_day_records[-1]
                if record is not None:
                    print("Never comes in here")
                    updated_record = self.__get_ohlc(record, ohlc)
                    updated_record['date'] = agg_datetime
                    last_day_records[-1] = updated_record
                else:
                    # TODO: Create a deep copy?
                    ohlc['date'] = agg_datetime
                    last_day_records.append(ohlc)

            # print("Recording data in DB" + str(tick_data))

    def strategy_runner(self, tick_data, timestamp, backfill=False):
        for strategy in self.stratagies:
            order_details = strategy.run(tick_data, timestamp, backfill=backfill)
        pass

    def shutdown(self):
        self.tradingAPI.shutdown()
