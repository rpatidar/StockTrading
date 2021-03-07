import pandas as pd

from db.storage import StorageHandler
from db.tradebook import TradeBook
from strategy.strategy import Strategy
from talipp.indicators import SMA, RSI,ADX
from talipp.ohlcv import OHLCV


class RSIMeanReversion(Strategy):
    """
        1.  Ignore OHLC and adx relatd code here
        2.  Need to fix some edge cases
    """
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
        self.day_ohlc = {}
        self.starting_amount = 20000

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
                self.starting_amount += (position['entry_price'] - position['exit_price'] + position['entry_price']) * position["quantity"]
                print("PL," ,symbol , ",", str(pl),str(self.total_pl), self.starting_amount)
        ohlc = self.days_prices[instrument_token]
        #Ignore ADX, not used as of now.
        adx_ohlc = OHLCV(open=ohlc['open'], close=ohlc['close'], high=ohlc['high'], low=ohlc['low'], volume=ohlc['volume'])
        if inst_data == None:
            inst_data = {
                "numdays": 0,
                "sma200": SMA(200),
                "rsi2": RSI(period=2),
                "adx" : ADX(30,30),
                "daygain": 0
            }
            self.instrument_data[instrument_token] = inst_data
        inst_data["numdays"] += 1
        closing_price = self.days_prices[instrument_token]['close']
        inst_data["sma200"].add_input_value(closing_price)
        inst_data["rsi2"].add_input_value(closing_price)
        inst_data["adx"].add_input_value(OHLCV(open=ohlc['open'], close=ohlc['close'], high=ohlc['high'], low=ohlc['low'], volume=ohlc['volume']))

        inst_data["daygain"] = ((self.days_prices[instrument_token]['close'] - self.days_prices[instrument_token][
            'open']) / self.days_prices[instrument_token]['open']) * 100

        # print(inst_data["rsi2"][-1])
        #print(self.days_prices[instrument_token])

        if len(inst_data["sma200"]) > 0 and inst_data["sma200"][-1] < self.days_prices[instrument_token]['close'] and \
                inst_data["rsi2"][-1] > 50 and \
                inst_data['daygain'] > 3:
            #print("Criteria meet on the date:" + str(date))
            #print(inst_data['adx'][-1])
            self.setup_meets_criteria[instrument_token] = {
                "setup": True,
                "sell_trigger_limit_price": self.days_prices[instrument_token]['close'] * 1.012
            }
        else:
            self.setup_meets_criteria[instrument_token] = {
                "setup": False
            }

        # if(len(inst_data["sma200"]) > 0):
        # print(inst_data["sma200"])
        self.cache_data[instrument_token] = None
        self.days_prices[instrument_token] = None
        #self.day_ohlc[instrument_token] = None
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
            #This is done to avoid running it on every tick, not useful for now, need to be improved
            if self.last_ticks_time.get(instrument_token) is not None and self.last_ticks_time.get(
                    instrument_token) == current_minute:
                continue
            setup_details = self.setup_meets_criteria.get(instrument_token)
            day_ohlc = self.days_prices.get(instrument_token)

            if day_ohlc is None:
                first_candle = True
                day_ohlc = {
                                "open": trading_data["open"],
                                "high": trading_data["high"],
                                "low": trading_data["low"],
                                "volume": trading_data["volume"]
                }
                self.days_prices[instrument_token] = day_ohlc
            else:
                day_ohlc['high'] = max(day_ohlc['high'], trading_data['high'])
                day_ohlc['low'] = min(day_ohlc['low'], trading_data['low'])
                day_ohlc['volume'] = day_ohlc['volume'] + trading_data['volume']
                day_ohlc['close'] = trading_data['close']

                # if setup_details is not None:
                #     if setup_details['setup'] and setup_details['sell_trigger_limit_price'] < day_ohlc['open']:
                #         #Invalid setup
                #         print("Invalid as gap up opening")
                #         setup_details['setup'] = False
            if setup_details is not None:
                factor = 0
                if position is None:
                    if last_close is not None and setup_details['setup'] and \
                            trading_data['low'] < setup_details['sell_trigger_limit_price'] < trading_data['high']:
                        quantity = int((self.starting_amount/(factor+1)) / setup_details['sell_trigger_limit_price'])
                        if quantity > 1:
                            position = {
                                "entry_price": setup_details['sell_trigger_limit_price'],
                                "target": setup_details['sell_trigger_limit_price'] * 0.94,
                                "stop_loss": setup_details['sell_trigger_limit_price'] * 1.025,
                                "quantity": quantity,
                                "pyramidding_done" : False
                            }
                            self.starting_amount = self.starting_amount - setup_details['sell_trigger_limit_price'] * quantity
                            print("Order meets the criteria"+ str(current_minute))
                else:
                    if position.get("exit_price") is None:
                        if position["target"] > trading_data['low']:
                            # print("Target meet")
                            position["exit_price"] = position["target"]

                        elif position["stop_loss"] < trading_data['high']:
                            # print("Stoploss hit")
                            position["exit_price"] = position["stop_loss"]
                        #Ignore this section this is created for pyramidding
                        elif factor > 0 and position["pyramidding_done"] == False and position["entry_price"] * 1.025  < trading_data['high']:
                            #
                            #Pyramidding one more order with one more quantity as the risk/reward is much lower now.
                            if self.starting_amount > position["entry_price"] * 1.025 * position["quantity"] * factor:
                                self.starting_amount = self.starting_amount - position["entry_price"] * 1.025 * factor * position["quantity"]
                                position["entry_price"]  = position["entry_price"] * ((1+factor*1.025))/(factor+1)
                                position["quantity"] +=   factor  * position["quantity"]
                                position["pyramidding_done"] = True


            if self.last_date.get(instrument_token) != current_date:
                day_opening = trading_data['open']
                self.days_prices[instrument_token]['open'] = trading_data['open']
            self.last_date[instrument_token] = current_date
            self.last_ticks_time[instrument_token] = current_minute
            self.days_prices[instrument_token]['close'] = trading_data['close']
            self.cache_data[instrument_token] = (trading_data['close'], day_opening, position)
