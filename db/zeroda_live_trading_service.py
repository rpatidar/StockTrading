import logging
import sys
import pandas
from messenger.tele_messenger import Messenger
from broker.zerodha.zeroda_base import ZerodhaServiceBase
import requests
import json
import os
import threading
import datetime
from tabulate import tabulate


class ZerodhaLiveTradingService(ZerodhaServiceBase):
    """
    Helper utitlity to place the live orders in Zerodha
    """

    def __init__(self, credential, configuration):
        # Ignore the credentail as its hard coded inside as of now.
        super(ZerodhaLiveTradingService, self).__init__(credential, configuration)
        self.margin_info = pandas.read_csv(
            "resource/zeroda_margin_stocks.csv", index_col="script"
        )

        self.mode = None
        if configuration:
            self.mode = configuration.get("mode")
        self.messenger = Messenger(self.mode)
        self.quantity_tracker = {}
        self.ongoing_trades = 0
        self.history = {}
        self.open_positions = {}

    def enter(
        self, trade_type, instrument_token, date, price, strategy, strategycontext
    ):
        # TODO: move this to the actual class
        if self.proxy:
            r = requests.post(
                self._url("/enter"),
                json={
                    "type": trade_type,
                    "instrument_token": instrument_token,
                    "date": date.timestamp(),
                    "price": price,
                    "strategy": strategy,
                    "strategycontext": strategycontext,
                },
            )
            r.raise_for_status()
            return

        symbol, exchange = self.get_symbol_and_exchange(instrument_token)
        # if self.ongoing_trades > 10:
        #     logging.info("Too many trades, not taking any trades for now")
        #     return

        if not symbol in self.margin_info.index:
            logging.info(
                "Can't entry trade with margin for the Stock {}".format(symbol)
            )
            return

        # This logic should be updated by checking the actual amount and the leverage we can have self.margin_info[symbol]['leverage_margin']
        self.quantity_tracker[symbol] = (
            int(5000 / price) if price < 5000 and self.ongoing_trades < 5 else 1
        )
        # self.quantity_tracker[symbol] = 1

        self.log_trade(trade_type, "Entry", date, price, symbol)

        try:
            # TODO: Try placing a limit order instead of market order
            # Backtest with last 1 year of data to see if its profimaking idea.
            order_id = "RandomIdEnter"
            if self.mode == "live":
                order_id = self.kite.place_order(
                    tradingsymbol=symbol,
                    exchange=exchange,
                    transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                    quantity=self.quantity_tracker[symbol],
                    order_type=self.kite.ORDER_TYPE_MARKET,
                    product=self.kite.PRODUCT_MIS,
                    variety=self.kite.VARIETY_REGULAR,
                )
            self.ongoing_trades = self.ongoing_trades + 1
            logging.info("entry Order placed. ID is: {}".format(order_id))
            self.open_positions[symbol] = {
                "entry_price": price,
                "date": date,
                "execution_info": strategycontext,
                "strategy": strategy,
                "type": type,
                "quantity": self.quantity_tracker[symbol],
            }
        except:
            e = sys.exc_info()
            logging.info(
                "Error while placing the entry Order for {0}".format(symbol), exc_info=e
            )
            self.messenger.send_message(
                "Error while placing the BUY Order for {0}\n with Exception : {1}".format(
                    symbol, str(e)
                )
            )

    def exit(
        self, trade_type, instrument_token, date, price, strategy, strategycontext
    ):
        import time

        if self.proxy:
            r = requests.post(
                self._url("/exit"),
                json={
                    "type": trade_type,
                    "instrument_token": instrument_token,
                    "date": date.timestamp(),
                    "price": price,
                    "strategy": strategy,
                    "strategycontext": strategycontext,
                },
            )
            r.raise_for_status()
            return

        symbol, exchange = self.get_symbol_and_exchange(instrument_token)

        if not symbol in self.margin_info.index:
            logging.info("Can't SEL trade with margin for the Stock {}".format(symbol))
            return

        self.log_trade(trade_type, "Exit", date, price, symbol)
        try:
            order_id = "RandomIdExit"
            if self.mode == "live":
                order_id = self.kite.place_order(
                    tradingsymbol=symbol,
                    exchange=exchange,
                    transaction_type=self.kite.TRANSACTION_TYPE_SELL,
                    quantity=self.quantity_tracker[symbol],
                    order_type=self.kite.ORDER_TYPE_MARKET,
                    product=self.kite.PRODUCT_MIS,
                    variety=self.kite.VARIETY_REGULAR,
                )

            logging.info("Sell Order placed. ID is: {}".format(order_id))
            open_position = self.open_positions.get(symbol)
            enter_date = open_position["date"]
            exit_date = date
            self.history.setdefault(symbol, []).append(
                {
                    "entry_price": open_position["entry_price"],
                    "exit_price": price,  # raw_trading_data[len(h) - 1]['close'],
                    "execution_info": open_position["execution_info"],
                    "entry_time": enter_date,
                    "exit_time": exit_date,
                    "type": open_position["type"],
                    "quantity": open_position["quantity"],
                }
            )

            self.open_positions["symbol"] = None
        except:
            e = sys.exc_info()
            logging.info(
                "Error while placing the SELL Order for {0}".format(symbol), exc_info=e
            )
            self.messenger.send_message(
                "Error while placing the SELL Order for {0}\n with Exception : {1}".format(
                    symbol, str(e)
                )
            )

    def log_trade(self, trade_type, fnc_type, date, price, symbol):
        f = [
            ["Symbol", symbol],
            ["TradeType", trade_type],
            ["Function", fnc_type],
            ["Date", date.strftime("%y-%m-%d")],
            ["Time", date.strftime("%H-%M-%S")],
            ["Price", price],
        ]
        f = tabulate(f)
        logging.info(f)
        self.messenger.send_message(f)

    @staticmethod
    def to_readable_date(d):
        if float == type(d):
            return datetime.datetime.fromtimestamp(d)
        return d

    def get_history(self):
        if self.mode == None or self.mode == "live":
            return self.history
        with open("./tmp/summery/history.json", "r") as o:
            return json.load(o)

    def summery(self):
        if not os.path.exists("./tmp/summery"):
            os.mkdir("./tmp/summery")
        file = open("./tmp/summery/history.json", "w")
        file.write(json.dumps(self.history, indent=1, default=str))
        file.close()
