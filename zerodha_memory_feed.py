from kiteconnect import KiteConnect
import datetime
from pyalgotrade.bar import BasicBar
from pyalgotrade.bar import Frequency
import pickle
import json, os


def date_ranges(d1_str, d2_str, days=60):
    format_str = '%Y-%m-%d'  # The format
    d1_date = datetime.datetime.strptime(d1_str, format_str) if type(d1_str) == str  else d1_str
    d2_date = datetime.datetime.strptime(d2_str, format_str) if type(d2_str) == str else d2_str

    from datetime import timedelta
    diffdays = (d2_date - d1_date).days
    last_start = 0
    dlist = []
    first = True
    for r in range(0, diffdays + days, days):
        next_date = min(r, diffdays)
        if first or next_date > last_start:
            dlist.append(((d1_date + timedelta(days=last_start)).date(), (d1_date + timedelta(days=next_date)).date()))
        last_start = next_date + 1
        first = False
    return dlist


class ZerodhaFeed:

    def __init__(self, api_key_params=None, api_token_params=None, kite=None):
        self.instrument_file = "./tmp/instruments"
        if kite != None:
            self.kite = kite
        # else:
        #     if (api_token_params == None):
        #         api_key_params, _, api_token_params = _load_token()
        #
        #     self.kite = KiteConnect(api_key_params, access_token=api_token_params)
        # print("Connecting with following " + api_key_params + " " + api_token_params)
        self.instruments = None
        self.tmp_dir = "./tmp/"

    def get_history(self, stock, from_date, to_date, exchange="NSE", agg_type="day"):

        if self.instruments is None:
            if os.path.exists(self.instrument_file):
                self.instruments = pickle.load(open(self.instrument_file, "rb"))
            else:
                self.instruments = self.kite.instruments()
                filehandler = open(self.instrument_file, "wb")
                pickle.dump(self.instruments, filehandler)
                filehandler.close()

        inst = None
        for inst_data in self.instruments:
            if inst_data['tradingsymbol'] == stock and inst_data['exchange'] == exchange:
                inst = inst_data['instrument_token']

        if inst is None:
            raise Exception("Can't find instrument : " + stock)
        stock_data = []
        for dranges in date_ranges(from_date, to_date):
            print("Downloading:" + str(dranges[0]) + ":" + str(dranges[1]))
            stock_data.extend(self._local_get_historical_data(stock, dranges, inst))
        return stock_data

    def _local_get_historical_data(self, stock, dranges, inst):
        stock_file_name = self.tmp_dir + stock \
                          + "_" \
                          + str(inst) \
                          + "_" \
                          + str(dranges[0]) \
                          + "---" \
                          + str(dranges[1])

        if os.path.exists(stock_file_name):
            return pickle.load(open(stock_file_name, "rb"))

        data = self.kite.historical_data(
            inst,
            dranges[0],
            dranges[1],
            "minute",
            continuous=False,
            oi=False)
        filehandler = open(stock_file_name, "wb")
        pickle.dump(data, filehandler)
        filehandler.close()
        return data

    # def get_feed(self, stock, from_date, to_date, exchange="NSE", agg_type="day"):
    #
    #     trading_data = self.get_history(stock, from_date, to_date, exchange, agg_type)
    #     d = []
    #     for t in trading_data:
    #         d.append((BasicBar(t['date'], t['open'], t['high'], t['low'], t['close'], t['volume'], t['close'],
    #                            Frequency.MINUTE)))
    #     return d
