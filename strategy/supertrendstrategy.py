from kiteconnect import KiteConnect
from math import floor, ceil
import datetime
import pandas as pd
import numpy as np
import sys
import os
import time

from db.tradebook import TradeBook
from strategy.strategy import Strategy
import pandas as pd
from db.storage import StorageHandler

risk_per_trade = 100 # if stoploss gets triggers, you loss will be this, trade quantity will be calculated based on this
supertrend_period = 30
supertrend_multiplier=3
candlesize = '5minute'

# Source for tech indicator : https://github.com/arkochhar/Technical-Indicators/blob/master/indicator/indicators.py
def EMA(df, base, target, period, alpha=False):
    """
    Function to compute Exponential Moving Average (EMA)
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        base : String indicating the column name from which the EMA needs to be computed from
        target : String indicates the column name to which the computed data needs to be stored
        period : Integer indicates the period of computation in terms of number of candles
        alpha : Boolean if True indicates to use the formula for computing EMA using alpha (default is False)
    Returns :
        df : Pandas DataFrame with new column added with name 'target'
    """

    con = pd.concat([df[:period][base].rolling(window=period).mean(), df[period:][base]])

    if (alpha == True):
        # (1 - alpha) * previous_val + alpha * current_val where alpha = 1 / period
        df[target] = con.ewm(alpha=1 / period, adjust=False).mean()
    else:
        # ((current_val - previous_val) * coeff) + previous_val where coeff = 2 / (period + 1)
        df[target] = con.ewm(span=period, adjust=False).mean()

    df[target].fillna(0, inplace=True)
    return df

def ATR(df, period, ohlc=['open', 'high', 'low', 'close']):
    """
    Function to compute Average True Range (ATR)
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR)
            ATR (ATR_$period)
    """
    atr = 'ATR_' + str(period)

    # Compute true range only if it is not computed and stored earlier in the df
    if not 'TR' in df.columns:
        df['h-l'] = df[ohlc[1]] - df[ohlc[2]]
        df['h-yc'] = abs(df[ohlc[1]] - df[ohlc[3]].shift())
        df['l-yc'] = abs(df[ohlc[2]] - df[ohlc[3]].shift())

        df['TR'] = df[['h-l', 'h-yc', 'l-yc']].max(axis=1)

        df.drop(['h-l', 'h-yc', 'l-yc'], inplace=True, axis=1)

    # Compute EMA of true range using ATR formula after ignoring first row
    EMA(df, 'TR', atr, period, alpha=True)

    return df

def SuperTrend(df, period=supertrend_period, multiplier=supertrend_multiplier, ohlc=['open', 'high', 'low', 'close']):
    """
    Function to compute SuperTrend
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        multiplier : Integer indicates value to multiply the ATR
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR), ATR (ATR_$period)
            SuperTrend (ST_$period_$multiplier)
            SuperTrend Direction (STX_$period_$multiplier)
    """

    ATR(df, period, ohlc=ohlc)
    atr = 'ATR_' + str(period)
    st = 'ST' #+ str(period) + '_' + str(multiplier)
    stx = 'STX' #  + str(period) + '_' + str(multiplier)

    """
    SuperTrend Algorithm :
        BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
        BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR
        FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND))
                            THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)
        FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND)) 
                            THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)
        SUPERTREND = IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
                        Current FINAL UPPERBAND
                    ELSE
                        IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
                            Current FINAL LOWERBAND
                        ELSE
                            IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
                                Current FINAL LOWERBAND
                            ELSE
                                IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
                                    Current FINAL UPPERBAND
    """

    # Compute basic upper and lower bands
    df['basic_ub'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 + multiplier * df[atr]
    df['basic_lb'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 - multiplier * df[atr]

    # Compute final upper and lower bands
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    for i in range(period, len(df)):
        df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or \
                                                         df[ohlc[3]].iat[i - 1] > df['final_ub'].iat[i - 1] else \
        df['final_ub'].iat[i - 1]
        df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or \
                                                         df[ohlc[3]].iat[i - 1] < df['final_lb'].iat[i - 1] else \
        df['final_lb'].iat[i - 1]

    # Set the Supertrend value
    df[st] = 0.00
    for i in range(period, len(df)):
        df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[
            i] <= df['final_ub'].iat[i] else \
            df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] > \
                                     df['final_ub'].iat[i] else \
                df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] >= \
                                         df['final_lb'].iat[i] else \
                    df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] < \
                                             df['final_lb'].iat[i] else 0.00

        # Mark the trend direction up/down
    df[stx] = np.where((df[st] > 0.00), np.where((df[ohlc[3]] < df[st]), 'down', 'up'), np.NaN)

    # Remove basic and final bands from the columns
    df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)

    df.fillna(0, inplace=True)
    return df

class SuperTrendStrategy(Strategy):
    def __init__(self):
        super(SuperTrendStrategy, self).__init__()
        self.tb = TradeBook()
        self.open_position = {}
        self.pl = {}
        self.last_date = {}
        self.last_closing_price = {}
        self.invalid_setup = {}

    def close_day(self, date, instrument_token, backfill=False):
        if backfill:
            return
        sh = StorageHandler()
        trading_sevice = self.tb.get_trading_service();
        symbol, _ = trading_sevice.get_symbol_and_exchange(instrument_token)

        stock_history = StorageHandler().get_db()[instrument_token]["1minute"]
        last_date = sorted(stock_history.keys())[-1]
        closing_price =  stock_history[last_date][-1]['close']
        position = self.open_position.get(instrument_token)
        if position is not None:
            if position.get('exit_price') is None:
                #print("Day Closing exit")
                position['exit_price'] = closing_price
                position['exit_timestamp'] = "DayClosure"
            tracking_pl= "ABC"
            stock_pl = self.pl.get(tracking_pl)
            if stock_pl == None:
                stock_pl = {'pl' : 0, 'brokerage': 0}
                self.pl[tracking_pl] = stock_pl
            current_pl = (position['exit_price']  - position['entry_price'] ) * position['quantity']
            current_brokerge =  position['quantity'] * ( position['entry_price'] + position['exit_price'] ) * 0.0004
            stock_pl['pl']= stock_pl['pl'] + current_pl
            stock_pl['brokerage'] = stock_pl['brokerage'] + current_brokerge
            #print(position)
            plfile = open("./pl.csv", "a")
            plfile.write(str(symbol) + "," + str(position['entry_timestamp']) +"," + str(position['exit_timestamp']) +","+ str(current_pl)  +"," + str(position['quantity'])+","  + str(position['entry_price'])+"," + str(position['exit_price']) +"\n")
            plfile.close()
            print(stock_pl)

        self.last_closing_price[instrument_token] = closing_price
        #invalid setup
        #Close
        self.open_position[instrument_token] = None
        self.invalid_setup[instrument_token] = None

    def get_last_n_days_ticks(self, instrument_token, last_n_days=10):
        stock_history = StorageHandler().get_db()[instrument_token]["1minute"]
        dates = sorted(stock_history.keys())
        if len(dates) > last_n_days:
            dates = dates[-last_n_days:]
            records = []
            for d in dates:
                records.extend(stock_history[d])
            df = pd.DataFrame.from_dict(records, orient='columns', dtype=None)
            if not df.empty:
                #df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
                df['date'] = df['date'].astype(str).str[:-6]
                df['date'] = pd.to_datetime(df['date'])
                df = SuperTrend(df)
                return df
        return None

    def run(self, ticks, timestamp, backfill=False):

        for tick_data in ticks:
            instrument_token = tick_data["instrument_token"]
            trading_data = tick_data["ohlc"]
            current_date = tick_data["ohlc"]['date'].date()
            histdata = self.get_last_n_days_ticks(instrument_token, last_n_days=10)
            if histdata is None:
                print("*****not enfough data, continue")
                continue
            if len(histdata.high.values) < 3:
                print("#####not enfough candle")
                continue
            super_trend = histdata.STX.values
            lastclose = histdata.close.values[-1]
            stoploss_buy = histdata.low.values[-3] # third last candle as stoploss
            stoploss_sell = histdata.high.values[-3] # third last candle as stoploss
            # print(histdata)
            # raise Exception("Temp failure")
            #print(stoploss_buy)
            if stoploss_buy > lastclose * 0.996:
                stoploss_buy = lastclose * 0.996 # minimum stoploss as 0.4 %

            if stoploss_sell < lastclose * 1.004:
                stoploss_sell = lastclose * 1.004 # minimum stoploss as 0.4 %
            #print("lastclose",lastclose)
            #print("stoploss abs",stoploss)
            #print(tickerlist[i],lastclose,super_trend[-4:])
            position = self.open_position.get(instrument_token)
            if position is None:
                if super_trend[-1]=='up' and super_trend[-3]=='down' and super_trend[-4]=='down' and super_trend[-5]=='down' and super_trend[-6]=='down':
                    stoploss_buy = lastclose - stoploss_buy
                    #print("stoploss delta", stoploss)

                    quantity = floor(max(1, (risk_per_trade/stoploss_buy)))
                    target = stoploss_buy*3 # risk reward as 3

                    price = int(100 * (floor(lastclose / 0.05) * 0.05)) / 100
                    stoploss_buy = int(100 * (floor(stoploss_buy / 0.05) * 0.05)) / 100
                    quantity = int(quantity)
                    target = int(100 * (floor(target / 0.05) * 0.05)) / 100

                    #print(histdata.to_string())
                    self.open_position[instrument_token] = {"quantity": quantity,
                                                            # This is making a huge differrence, need to close on this.
                                                            "entry_price": price,
                                                            "stop_loss": price - stoploss_buy,
                                                            "target": price + target,
                                                            "entry_timestamp": timestamp}
                    print(self.open_position[instrument_token])

            elif position.get('exit_price') is None:
                current_price = tick_data['ohlc']['high']

                if current_price > position['target']:
                    print("Closing the position as target met:" + str(position['target']))
                    position['exit_price'] = position['target']
                    position['exit_timestamp'] = timestamp
                if  current_price < position['stop_loss']:
                    print("Closing the position as stoploss hit:" + str(position['target']))
                    position['exit_price'] = position['stop_loss']
                    position['exit_timestamp'] = timestamp

