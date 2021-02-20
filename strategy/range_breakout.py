import logging


from db.tradebook import TradeBook
from strategy.strategy import Strategy
import pandas as pd
from db.storage import StorageHandler


class RangeBreakout(Strategy):
    def __init__(self):

        super(RangeBreakout, self).__init__()
        self.tb = TradeBook()
        self.open_position = {}
        self.pl = {}
        self.last_date = {}
        self.last_closing_price = {}
        self.invalid_setup = {}
        self.cached_date = {"reference_date": None, "last_trading_date": None}

    def _get_last_trading_date(self, reference_date, inst_token):

        sh = StorageHandler()
        if self.cached_date["reference_date"] == reference_date:
            return self.cached_date["last_trading_date"]

        trading_dates = sorted(sh.get_db()[inst_token]["1minute"].keys())
        last_trading_date = None
        for d in trading_dates:
            if d < reference_date:
                last_trading_date = d
        if last_trading_date != None:
            self.cached_date["reference_date"] = reference_date
            self.cached_date["last_trading_date"] = last_trading_date
        return last_trading_date


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


    def run(self, ticks, timestamp, backfill=False):

        for tick_data in ticks:
            instrument_token = tick_data["instrument_token"]
            trading_data = tick_data["ohlc"]
            current_date = tick_data["ohlc"]['date'].date()
            last_date = self.last_date.get(instrument_token)
            #Need to handle the first candle for streaming data seprately
            first_candle = last_date != current_date
            self.last_date[instrument_token] = current_date
            service = self.tb.get_trading_service()
            sh = StorageHandler()
            stock_history = sh.get_db()[instrument_token]["1minute"] #self.cache[instrument_token]

            if last_date is None or first_candle and trading_data['open'] > self.last_closing_price[instrument_token] * 1.01 :
                self.invalid_setup[instrument_token] = True

            if self.invalid_setup.get(instrument_token):
                continue

            last_trading_date = self._get_last_trading_date(current_date, instrument_token)
            last_trading_data = None
            if last_trading_date is not None:
                last_trading_data = stock_history[last_trading_date]
            current_day_trading_data = stock_history[current_date]
            position = self.open_position.get(instrument_token)
            if position is None:
                lh, ll, lv = None, None, 0
                if last_trading_data != None:
                    #This will not work in real time , backtesting we are using 1 minute agregates which have fixed size,
                    #realtime tick data is variable, we need to fix it accordingly
                    k = len(current_day_trading_data)
                    max_len = len(last_trading_data)
                    if len(last_trading_data) < len(current_day_trading_data):
                        #Some invalid case.
                        continue

                    for i in range(max_len):
                        d = last_trading_data[i]
                        if lh is None:
                            lh = d['high']
                        if ll is None:
                            ll = d['low']
                        lh = max(lh, d['high'])
                        ll = min(ll, d['low'])
                        if i < k:
                            lv = lv + d['volume']

                    vol_today = 0
                    for todays_tick in current_day_trading_data:
                        vol_today = vol_today + todays_tick['volume']
                    #This is an assumption that our tick data in real time and we meet a buy order on certain price when it occures.
                    if trading_data['high'] > lh * 1.01 and vol_today > lv * 2:
                        stop_loss = trading_data['close'] * 0.985
                        stop_loss_for_quantity =  (lh + ll) / 2
                        quantity = int(1000/(stop_loss_for_quantity - ll))
                        if quantity * trading_data['close'] > 200000:
                            quantity = int(200000/trading_data['close'])
                        target = lh * 1.04

                        self.open_position[instrument_token] = {"quantity": quantity,
                                                                #This is making a huge differrence, need to close on this.
                                                                "entry_price":  lh * 1.01, # trading_data['close'],
                                                                "stop_loss": stop_loss,
                                                                "target": target,
                                                                "entry_timestamp" : timestamp,
                                                                'last_high': lh,
                                                                'last_low': ll,
                                                                'high' : tick_data['ohlc']['high']
                                                                }

            elif position.get('exit_price') is None:
                current_price = tick_data['ohlc']['close']

                if current_price < position['stop_loss'] or current_price > position['target']:
                    print("Closing the position as target met:" + str(current_price))
                    position['exit_price'] = current_price
                    position['exit_timestamp'] = timestamp