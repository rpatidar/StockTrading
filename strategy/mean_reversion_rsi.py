import pandas as pd

from db.storage import StorageHandler
from db.tradebook import TradeBook
from strategy.strategy import Strategy
from talipp.indicators import SMA, RSI


class RSIMeanReversion(Strategy):
    def __init__(self):
        super(RSIMeanReversion, self).__init__()
        self.tb = TradeBook()
        self.open_position = {}
        self.pl = {}
        self.last_ticks_time = {}
        self.last_date = {}
        self.days_prices = {}
        self.invalid_setup = {}
        self.price_data_for_days = 10
        self.total_pl = 0
        self.instrument_data = {}
        self.setup_meets_criteria = {}
        self.cache_data = {}
        self.total_pl = 0

    def close_day(self, date, instrument_token, backfill=False):

        inst_data = self.instrument_data.get(instrument_token)
        symbol, exchange = self.tb.get_trading_service().get_symbol_and_exchange(instrument_token)
        previous_cached_info = self.cache_data.get(instrument_token)
        if previous_cached_info != None:
            _, _, position = previous_cached_info
            if position != None:
                if position.get("exit_price") == None:
                    position["exit_price"] = self.days_prices[instrument_token]['close']
                pl = (position['entry_price'] - position['exit_price']) / position['entry_price'] * 100
                self.total_pl += pl

                print("PL," ,symbol , ",", str(pl),str(self.total_pl))

        if inst_data == None:
            inst_data = {
                "numdays": 0,
                "sma200": SMA(200),
                "rsi2": RSI(period=2),
                "daygain": 0
            }
            self.instrument_data[instrument_token] = inst_data

        inst_data["numdays"] += 1
        closing_price = self.days_prices[instrument_token]['close']
        inst_data["sma200"].add_input_value(closing_price)
        inst_data["rsi2"].add_input_value(closing_price)
        inst_data["daygain"] = ((self.days_prices[instrument_token]['close'] - self.days_prices[instrument_token][
            'open']) / self.days_prices[instrument_token]['open']) * 100

        # print(inst_data["rsi2"][-1])
        #print(self.days_prices[instrument_token])
        if len(inst_data["sma200"]) > 0 and inst_data["sma200"][-1] < self.days_prices[instrument_token]['close'] and \
                inst_data["rsi2"][-1] > 50 and \
                inst_data['daygain'] > 3:
            #print("Criteria meet on the date:" + str(date))
            self.setup_meets_criteria[instrument_token] = {
                "setup": True,
                "sell_trigger_limit_price": self.days_prices[instrument_token]['close'] * 1.01
            }
        else:
            self.setup_meets_criteria[instrument_token] = {
                "setup": False
            }

        # if(len(inst_data["sma200"]) > 0):
        # print(inst_data["sma200"])
        self.cache_data[instrument_token] = None
        if backfill:
            return

    def get_last_n_days_ticks(self, instrument_token, last_n_days=10):
        stock_history = StorageHandler().get_db()[instrument_token]["1minute"]
        dates = sorted(stock_history.keys())
        if len(dates) >= last_n_days:
            dates = dates[-last_n_days:]
            records = []
            for d in dates:
                records.extend(stock_history[d])
            df = pd.DataFrame.from_dict(records, orient='columns', dtype=None)
            return df
            # return records
        return None

    def run(self, ticks, timestamp, backfill=False):
        for tick_data in ticks:
            instrument_token = tick_data["instrument_token"]
            trading_data = tick_data["ohlc"]
            previous_cached_info = self.cache_data.get(instrument_token)

            last_close = None
            day_opening = None
            position = None
            if previous_cached_info is not None:
                last_close, day_opening, position = previous_cached_info

            current_date = tick_data["ohlc"]['date'].date()
            current_minute = tick_data["ohlc"]['date'].replace(second=0, microsecond=0)
            first_candle = False
            if self.last_ticks_time.get(instrument_token) is not None and self.last_ticks_time.get(
                    instrument_token) == current_minute:
                continue
            setup_details = self.setup_meets_criteria.get(instrument_token)
            day_ohlc = self.days_prices.get(instrument_token)

            if day_ohlc is None:
                first_candle = True
                day_ohlc = {}
                self.days_prices[instrument_token] = day_ohlc

                # if setup_details is not None:
                #     if setup_details['setup'] and setup_details['sell_trigger_limit_price'] < day_ohlc['open']:
                #         #Invalid setup
                #         print("Invalid as gap up opening")
                #         setup_details['setup'] = False
            if setup_details is not None:
                if position is None:
                    if last_close is not None and setup_details['setup'] and \
                            trading_data['low'] < setup_details['sell_trigger_limit_price'] < trading_data['high']:
                        position = {
                            "entry_price": setup_details['sell_trigger_limit_price'],
                            "target": setup_details['sell_trigger_limit_price'] * 0.94,
                            "stop_loss": setup_details['sell_trigger_limit_price'] * 1.03,
                        }
                        print("Order meets the criteria")
                else:
                    if position["target"] > trading_data['low']:
                        # print("Target meet")
                        position["exit_price"] = position["target"]

                    elif position["stop_loss"] < trading_data['high']:
                        # print("Stoploss hit")
                        position["exit_price"] = position["stop_loss"]

            if self.last_date.get(instrument_token) != current_date:
                day_opening = trading_data['open']
                self.days_prices[instrument_token]['open'] = trading_data['open']
            self.last_date[instrument_token] = current_date
            self.last_ticks_time[instrument_token] = current_minute
            self.days_prices[instrument_token]['close'] = trading_data['close']
            self.cache_data[instrument_token] = (trading_data['close'], day_opening, position)
