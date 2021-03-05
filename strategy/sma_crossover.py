from kiteconnect import KiteConnect
from math import floor, ceil
import datetime
import pandas as pd
import numpy as np
import sys
import os
import time
import pandas as pd
from db.tradebook import TradeBook
from strategy.strategy import Strategy
import pandas as pd
from db.storage import StorageHandler
import talib

risk_per_trade = 100 # if stoploss gets triggers, you loss will be this, trade quantity will be calculated based on this
supertrend_period = 30
supertrend_multiplier=3
candlesize = '5minute'


class SMACrossOver(Strategy):
    def __init__(self):
        super(SMACrossOver, self).__init__()
        self.tb = TradeBook()
        self.open_position = {}
        self.pl = {}
        self.last_ticks = {}
        self.last_date = {}
        self.last_closing_price = {}
        self.invalid_setup = {}
        self.price_data_for_days = 10
        self.total_pl = 0
    def close_day(self, date, instrument_token, backfill=False):
        if backfill:
            return
        # sh = StorageHandler()
        # trading_sevice = self.tb.get_trading_service();
        # symbol, _ = trading_sevice.get_symbol_and_exchange(instrument_token)
        #
        # stock_history = StorageHandler().get_db()[instrument_token]["1minute"]
        # trading_dates = sorted(stock_history.keys())[-self.price_data_for_days:]
        #
        # closing_price = stock_history[trading_dates[-1]][-1]['close']
        #
        # position = self.open_position.get(instrument_token)
        #
        # if position is not None:
        #
        #     if position.get('exit_price') is None:
        #         #print("Day Closing exit")
        #         position['exit_price'] = closing_price
        #         position['exit_timestamp'] = "DayClosure"
        #     tracking_pl= "ABC"
        #     stock_pl = self.pl.get(tracking_pl)
        #     if stock_pl == None:
        #         stock_pl = {'pl' : 0, 'brokerage': 0}
        #         self.pl[tracking_pl] = stock_pl
        #     current_pl = (position['exit_price']  - position['entry_price'] ) * position['quantity']
        #     current_brokerge =  position['quantity'] * ( position['entry_price'] + position['exit_price'] ) * 0.0004
        #     stock_pl['pl']= stock_pl['pl'] + current_pl
        #     stock_pl['brokerage'] = stock_pl['brokerage'] + current_brokerge
        #     #print(position)
        #     plfile = open("./pl.csv", "a")
        #     plfile.write(str(symbol) + "," + str(position['entry_timestamp']) +"," + str(position['exit_timestamp']) +","+ str(current_pl)  +"," + str(position['quantity'])+","  + str(position['entry_price'])+"," + str(position['exit_price']) +"\n")
        #     plfile.close()
        #     print(stock_pl)
        #
        # self.last_closing_price[instrument_token] = closing_price
        # #invalid setup
        # #Close
        # self.open_position[instrument_token] = None
        # self.invalid_setup[instrument_token] = None

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
            #return records
        return None

    def run(self, ticks, timestamp, backfill=False):

        for tick_data in ticks:
            instrument_token = tick_data["instrument_token"]
            trading_data = tick_data["ohlc"]
            current_date = tick_data["ohlc"]['date'].date()
            current_minute = tick_data["ohlc"]['date'].replace(second=0, microsecond=0)
            if self.last_ticks.get(instrument_token) is not None and self.last_ticks.get(instrument_token) == current_minute:
                continue

            self.last_ticks[instrument_token] = current_minute
            last_n_ticks = self.get_last_n_days_ticks(instrument_token, last_n_days=5)
            import talib
            if last_n_ticks is None:
                #print("None..")
                continue
            import numpy
            #print(self.tb.get_trading_service().get_symbol_and_exchange(instrument_token))
            sma = talib.SMA(last_n_ticks['close'].to_numpy(), timeperiod=300)
            sh = StorageHandler()
            stock_history = sh.get_db()[instrument_token]["1minute"]  # self.cache[instrument_token]
            current_day_trading_data = stock_history[current_date]
            last_sma_value = sma[-1]
            position = self.open_position.get(instrument_token)

            import math
            if math.isnan(last_sma_value):
                continue
            if position is None:
                if last_n_ticks.iloc[-2]['close'] < last_sma_value < last_n_ticks.iloc[-1]['close']:
                    price = current_day_trading_data[-1]['close']
                    quantity = 1
                    self.open_position[instrument_token] = {"quantity": quantity,
                                                            # This is making a huge differrence, need to close on this.
                                                            "entry_price": price,
                                                            "stop_loss": None,  # price - stoploss_buy,
                                                            "target": None,  # price + target,
                                                            "entry_timestamp": timestamp}
                    #print(self.open_position[instrument_token])
            elif position.get('exit_price') is None:
                if last_n_ticks.iloc[-2]['close'] < last_sma_value > last_n_ticks.iloc[-1]['close']:
                    position['exit_price'] = current_day_trading_data[-1]['close']
                    p = position['exit_price'] - position['entry_price']
                    self.total_pl = self.total_pl + p
                    print("Profit/Loss:" + str(self.total_pl) +"," + str(p))
                    self.open_position[instrument_token] = None
