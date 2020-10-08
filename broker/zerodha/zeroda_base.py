from kiteconnect import KiteConnect
from broker.trading_base import TradingService
import os, pickle, webbrowser
import datetime

tmp_dir = "tmp/"  # if os.name == "nt" else "/tmp/"
mock_file = tmp_dir + "/mock"
import logging

class ZerodhaServiceBase(TradingService):
    def __init__(self, credential, configuration):
        self.session_file = tmp_dir + "/session_file"
        super(ZerodhaServiceBase, self).__init__(credential, configuration)
        self.api_key = credential['api_key']
        self.api_secret = credential['api_secret']
        self.mock = int(open(mock_file, "r").read() if os.path.exists(mock_file) else "0")
        self._login()
        self.tmp_dir = tmp_dir
        self.instrument_file = tmp_dir + "/instruments"
        self._get_instrumentnts()

    def _login(self):
        if self.mock == 0:
            kite = KiteConnect(self.api_key, self.api_secret)
            token = self._load_token();
            if not token:
                webbrowser.open_new_tab(KiteConnect(self.api_key, self.api_secret).login_url())
                url = input("Enter Your token URL here")
                tmp_dir + "/session_file"
                data = kite.generate_session(url.split("request_token=")[1].split("&action")[0],
                                             api_secret=self.api_secret)
                token = data["access_token"]
                self._save_session(token)
            kite.set_access_token(token)
            self.access_token = token
            self.kite = kite

    def _load_token(self):
        import json
        if not os.path.exists(self.session_file):
            return None
        session_data = json.load(open(self.session_file, "r"))
        session_data['lastSessionDate'] = eval(session_data['lastSessionDate'])
        if session_data['lastSessionDate'] + datetime.timedelta(days=1) > datetime.datetime.now():
            return session_data['token']
        return None

    def _save_session(self, token):
        import json
        session = {'lastSessionDate': repr(datetime.datetime.now()), 'token': token}
        filehandler = open(self.session_file, 'w')
        json.dump(session, filehandler)
        filehandler.close()

    def _instrument_row(self, instruments, stock, exchange=None):
        exchanges = [exchange] if exchange else ["NSE", "BSE"]
        for exchange_name in exchanges:
            for instrument_data in instruments:
                if instrument_data['tradingsymbol'] == stock and instrument_data['exchange'] == exchange_name:
                    return instrument_data
        return None

    def _get_instrumentnts(self):
        if os.path.exists(self.instrument_file):
            self.instruments = pickle.load(open(self.instrument_file, "rb"))

        else:
            self.instruments = self.kite.instruments()
            filehandler = open(self.instrument_file, 'wb')
            pickle.dump(self.instruments, filehandler)
            filehandler.close()
        return self.instruments

    def _get_trading_data(self, stock_name, instrument_token, from_date, to_date):

        stock_file_name = self.tmp_dir + stock_name + "_" + str(instrument_token) + "_" + str(from_date) + "---" + str(
            to_date)
        if os.path.exists(stock_file_name):
            return pickle.load(open(stock_file_name, "rb"))

        else:
            trading_data = self.kite.historical_data(instrument_token, from_date, to_date, "minute", continuous=False,
                                                     oi=False)
            filehandler = open(stock_file_name, 'wb')
            pickle.dump(trading_data, filehandler)
            filehandler.close()
            return trading_data

    def execute_strategy_single_datapoint(self, instrument_token, stock, stock_config, backfill=False):
        logging.info("\n ==================================\nBacktesting now: {0} ".format(stock))
        from_date = stock_config['from']
        to_date = stock_config['to']
        trading_data = self._get_trading_data(stock, instrument_token, from_date, to_date)
        previous_date = None
        for trade_data in trading_data:
            # ohlc = copy.deepcopy(ohlcp)
            if previous_date != None and previous_date.date() != trade_data['date'].date():
                self.close_day(previous_date, instrument_token)
                previous_date = trade_data['date']
            previous_date = trade_data['date']
            decorated_trading_data = {'instrument_token': instrument_token, 'ohlc': trade_data}
            timestamp = trade_data['date']
            """5 minute aggregate publish"""
            """1 minute - irelevent"""
            self._update_tick_data([decorated_trading_data], timestamp, backfill=backfill)
        if previous_date != None:
            self.close_day(previous_date, instrument_token)
