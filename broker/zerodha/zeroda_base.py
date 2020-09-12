
from kiteconnect import KiteConnect
from broker.trading_base import TradingService
import os, pickle, webbrowser


tmp_dir = "c:/tmp/" if os.name == "nt" else "/tmp/"
mock_file = tmp_dir +"/mock"

class ZerodhaServiceBase(TradingService):
    def __init__(self, credential, configuration):
        super(ZerodhaServiceBase, self).__init__(credential, configuration)
        self.api_key = credential['api_key']
        self.api_secret = credential['api_secret']
        self.mock = int(open(mock_file,"r").read()  if os.path.exists(mock_file) else "0")
        self._login()
        self.tmp_dir  = tmp_dir
        self.instrument_file = tmp_dir+"/instruments"


    def _login(self):
        if self.mock == 0:
            kite = KiteConnect(self.api_key, self.api_secret)
            webbrowser.open_new_tab(KiteConnect(self.api_key, self.api_secret).login_url())
            url = input("Enter Your token URL here")
            data = kite.generate_session(url.split("request_token=")[1].split("&action")[0], api_secret=self.api_secret)
            kite.set_access_token(data["access_token"])
            self.access_token = data["access_token"]
            self.kite = kite

    def _instrument_row(self, instruments, stock, exchange='NSE'):
        for instrument_data in instruments:
            if instrument_data['tradingsymbol'] == stock and instrument_data['exchange'] == exchange:
                return instrument_data
        return None

    def _get_instrumentnts(self):
        if os.path.exists(self.instrument_file):
            self.instruments = pickle.load(open(self.instrument_file, "rb"))

        else:
            self.instruments = self.kite.instruments()
            filehandler  = open(self.instrument_file, 'wb')
            pickle.dump(self.instruments, filehandler)
            filehandler.close()
        return self.instruments

    def _get_trading_data(self, from_date, instrument_token, to_date):
        stock_file_name = self.tmp_dir + str(instrument_token)+"_"+str(from_date)+"---"+str(to_date)
        if os.path.exists(stock_file_name):
            return pickle.load(open(stock_file_name, "rb"))

        else:
            trading_data = self.kite.historical_data(instrument_token, from_date, to_date, "minute", continuous=False,
                                      oi=False)
            filehandler  = open(stock_file_name, 'wb')
            pickle.dump(trading_data, filehandler)
            filehandler.close()
            return trading_data