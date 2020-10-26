import datetime
import os
import pickle
import multiprocessing as mp
from kiteconnect import KiteConnect
from broker.zerodha.login_helper import prerequisite_multiprocess
import queue
from broker.trading_base import TradingService
import pytz

tmp_dir = "tmp/"  # if os.name == "nt" else "/tmp/"
mock_file = tmp_dir + "/mock"
import logging
import requests
import ratelimit
from backoff import on_exception, expo
from ratelimit import limits


class ZerodhaServiceBase(TradingService):
    def __init__(self, credential, configuration):
        super(ZerodhaServiceBase, self).__init__(credential, configuration)
        self.session_file = tmp_dir + "/session_file"
        self.api_key = credential["api_key"]
        self.api_secret = credential["api_secret"]
        self.warmup_disabled = False
        self.proxy = None
        if configuration:
            self.proxy = configuration.get("proxy")

        self.mock = int(
            open(mock_file, "r").read() if os.path.exists(mock_file) else "0"
        )
        self.access_token = prerequisite_multiprocess(self.api_key, self.api_secret)
        self.kite = KiteConnect(self.api_key, access_token=self.access_token)
        self.tmp_dir = tmp_dir
        self.instrument_file = tmp_dir + "/instruments"
        self.instruments = None
        self.cached_info = {}

    def _instrument_row(self, instruments, stock, exchange=None):
        exchanges = [exchange] if exchange else ["NSE", "BSE"]
        for exchange_name in exchanges:
            for instrument_data in instruments:
                if (
                    instrument_data["tradingsymbol"] == stock
                    and instrument_data["exchange"] == exchange_name
                ):
                    return instrument_data
        return None

    def get_symbol_and_exchange(self, instrument_token):
        token_info = self.cached_info.get(instrument_token)
        if token_info:
            return token_info
        instruments = self._get_instrumentnts()
        for instrument_data in instruments:
            if str(instrument_data["instrument_token"]) == str(instrument_token):
                self.cached_info[instrument_token] = (
                    instrument_data["tradingsymbol"],
                    instrument_data["exchange"],
                )
                return instrument_data["tradingsymbol"], instrument_data["exchange"]
        return None

    def _get_instrumentnts(self):
        if self.instruments:
            return self.instruments
        if self.proxy:
            import requests, json

            self.instruments = json.loads(
                json.dumps(requests.get(self.proxy + "/instruments").json())
            )
            return self.instruments
        if os.path.exists(self.instrument_file):
            self.instruments = pickle.load(open(self.instrument_file, "rb"))

        else:
            self.instruments = self.kite.instruments()
            filehandler = open(self.instrument_file, "wb")
            pickle.dump(self.instruments, filehandler)
            filehandler.close()
        return self.instruments

    def get_instruments(self):
        return self._get_instrumentnts()

    def get_trading_data(self, stock_name, instrument_token, from_date, to_date):
        return self._get_trading_data(stock_name, instrument_token, from_date, to_date)

    def _get_trading_data(self, stock_name, instrument_token, from_date, to_date):
        if self.proxy:
            r = requests.post(
                self._url("/historical_data"),
                json={
                    "instrument_token": instrument_token,
                    "from_date": from_date.timestamp(),
                    "to_date": to_date.timestamp(),
                    "aggregate_type": "minute",
                    "continous": False,
                    "oi": False,
                },
            )
            r.raise_for_status()
            hist_data = r.json()
            for d in hist_data:
                # TODO: Build mechanism to work indpenendent of timezones
                d["date"] = datetime.datetime.fromtimestamp(d["date"])
                # d["date"] = (
                #     datetime.datetime.fromtimestamp(d["date"])
                #     .replace(tzinfo=pytz.utc)
                #     .astimezone(tz=pytz.timezone("Asia/Kolkata"))
                # )

        stock_file_name = (
            self.tmp_dir
            + stock_name
            + "_"
            + str(instrument_token)
            + "_"
            + str(from_date)
            + "---"
            + str(to_date)
        )
        if os.path.exists(stock_file_name):
            return pickle.load(open(stock_file_name, "rb"))

        else:
            trading_data = self.rate_limited_historical_data_fetch(
                from_date, instrument_token, to_date
            )
            filehandler = open(stock_file_name, "wb")
            pickle.dump(trading_data, filehandler)
            filehandler.close()
            return trading_data

    @on_exception(expo, ratelimit.RateLimitException, max_tries=8)
    @limits(calls=3, period=1)
    def rate_limited_historical_data_fetch(self, from_date, instrument_token, to_date):
        trading_data = self.kite.historical_data(
            instrument_token,
            from_date,
            to_date,
            "minute",
            continuous=False,
            oi=False,
        )
        return trading_data

    def execute_strategy_single_stock_historical(
        self, instrument_token, stock, stock_config, backfill=False
    ):
        """
        Run trading on the historical data
        :param instrument_token:
        :param stock:
        :param stock_config:
        :param backfill:
            don't execute just mock the data to update the aggregates
        :return:
        """

        logging.info(
            "\n ==================================\nBacktesting now: {0} ".format(stock)
        )
        from_date = stock_config["from"]
        to_date = stock_config["to"]
        trading_data = self._get_trading_data(
            stock, instrument_token, from_date, to_date
        )
        previous_date = None
        for trade_data in trading_data:
            # Destroying the data immutability, should fix in the right way
            trade_data["date"] = trade_data["date"].replace(tzinfo=None)
            # ohlc = copy.deepcopy(ohlcp)
            if (
                previous_date != None
                and previous_date.date() != trade_data["date"].date()
            ):
                self.close_day(previous_date, instrument_token)
                previous_date = trade_data["date"]

            timestamp = previous_date = trade_data["date"]
            decorated_trading_data = {
                "instrument_token": instrument_token,
                "ohlc": trade_data,
            }
            """5 minute aggregate publish"""
            """1 minute - irelevent"""
            self._update_tick_data(
                [decorated_trading_data], timestamp, backfill=backfill
            )
        if previous_date != None:
            self.close_day(previous_date, instrument_token)

    def _url(self, path):
        return self.proxy + path

    def _preload_historical_data(self):
        """
        This is not the effective implementation, as of now blindly pre loading 1 week of data in memory.
        :return:
        #"""
        try:
            logging.info("Preloading the data for old dates")
            from datetime import datetime, timedelta

            todays_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            start_date = todays_date - timedelta(days=7)
            end_date = todays_date
            logging.info(
                "Preloading for following stocks:" + str(self.intresting_stocks)
            )
            for stock in self.intresting_stocks:
                instrument_data = self._instrument_row(self.get_instruments(), stock)
                if instrument_data == None:
                    logging.info("Didn't found the stock:" + str(stock))
                    continue
                logging.info("Backtesting for:" + str(stock))
                self.execute_strategy_single_stock_historical(
                    instrument_data["instrument_token"],
                    stock,
                    {"from": start_date, "to": datetime.now()},
                    backfill=True,
                )
                self.warmup_tracker[instrument_data["instrument_token"]] = True

            logging.info("Preloading the data Completed")
        except:
            logging.info("Some error happend")
            import traceback

            traceback.print_exc()

    def _get_ohlc(self, timestamp, tick):
        if tick.get("last_price"):
            return {
                "date": timestamp,
                "open": tick["last_price"],
                "high": tick["last_price"],
                "low": tick["last_price"],
                "close": tick["last_price"],
                }
        else:
            return tick.get('ohlc')
        
    def queue_based_tick_handler(self):
        while not self._check_shutdown_event():
            ticks, timestamp = None, None
            try:
                ticks, timestamp = self.q.get(block=True, timeout=1)
            except queue.Empty:
                continue

            # Only use stocks whose current data is loaded in memory already
            filtered_ticks = ticks
            if not self.warmup_disabled:
                filtered_ticks = []
                for t in ticks:
                    if t["instrument_token"] in self.warmup_tracker:
                        filtered_ticks.append(t)

            decorated_ticks = [
                {
                    "instrument_token": tick["instrument_token"],
                    "ohlc": self._get_ohlc(timestamp, tick),
                }
                for tick in filtered_ticks
            ]

            logging.info("Updated ticks data :" + str(decorated_ticks))
            self._update_tick_data(decorated_ticks, timestamp)
            if type(self.q) != mp.queues.Queue:
                self.q.task_done()
