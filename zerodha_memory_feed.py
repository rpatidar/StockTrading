import datetime
import os
import pickle


def date_ranges(d1_str, d2_str, days=60):
    format_str = '%Y-%m-%d'  # The format
    d1_date = datetime.datetime.strptime(d1_str, format_str) if type(d1_str) == str else d1_str
    d2_date = datetime.datetime.strptime(d2_str, format_str) if type(d2_str) == str else d2_str

    if type(d1_date) == datetime.date:
        d1_date = datetime.datetime(
            year=d1_date.year,
            month=d1_date.month,
            day=d1_date.day,
        )
        d2_date = datetime.datetime(
            year=d2_date.year,
            month=d2_date.month,
            day=d2_date.day,
        )

    from datetime import timedelta
    diffdays = (d2_date - d1_date).days
    last_start = 0
    dlist = []
    first = True
    for r in range(0, diffdays + days, days):
        next_date = min(r, diffdays)
        if first or next_date >= last_start:
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
        # Bad way to determine if to cache the last date or not to avoid the crashesh and resumes.
        # Can fix with some other better Params.
        last_date_cachable = True
        for dranges in date_ranges(from_date, to_date):
            stock_data.extend(self._local_get_historical_data(stock, dranges, inst))
        return stock_data

    def _local_get_historical_data(self, stock, dranges, inst):

        records = []
        missing_date_index = 0
        missing = False
        dates = date_ranges(dranges[0], dranges[1], days=1)
        for dd in dates:
            file_path = self.get_single_day_stock_cache_file_name(inst, dd[0], stock)
            if os.path.exists(file_path):
                records.extend(pickle.load(open(file_path, "rb")))
            else:
                missing = True
                break
            missing_date_index += 1

        if missing == False:
            return records

        print(stock + " Downloading:" + str(dranges[0]) + ":" + str(dranges[1]))
        records = self.kite.historical_data(
            inst,
            dranges[0],
            dranges[1],
            "minute",
            continuous=False,
            oi=False)
        date_to_records = {}

        for d in records:
            date_to_records.setdefault(d['date'].date(), []).append(d)

        for dd in dates:
            rec = date_to_records.get(dd[0])
            if rec == None:
                rec = []
            if not (dd[1] == datetime.datetime.now().date() and  datetime.datetime.now() > datetime.datetime.now().replace(hour=16, minute=0, second=0)):
                self.dump_a_day_data_to_file(rec, inst, dd[0], stock)

        return records

    def dump_a_day_data_to_file(self, data, inst, last_date, stock):
        single_day_stock_file_name = self.get_single_day_stock_cache_file_name(inst, last_date, stock)
        filehandler = open(single_day_stock_file_name, "wb")
        pickle.dump(data, filehandler)
        filehandler.close()

    def get_single_day_stock_cache_file_name(self, inst, last_date, stock):
        return self.tmp_dir + stock \
               + "_singleday_" \
               + str(inst) \
               + "_" \
               + str(last_date)

    # def get_feed(self, stock, from_date, to_date, exchange="NSE", agg_type="day"):
    #
    #     trading_data = self.get_history(stock, from_date, to_date, exchange, agg_type)
    #     d = []
    #     for t in trading_data:
    #         d.append((BasicBar(t['date'], t['open'], t['high'], t['low'], t['close'], t['volume'], t['close'],
    #                            Frequency.MINUTE)))
    #     return d
