import logging
import sys
import pandas
from messenger.tele_messenger import send_message
from broker.zerodha.zeroda_base import ZerodhaServiceBase
import requests
import json
import os
import threading
import datetime


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

        self.quantity_tracker = {}
        self.ongoing_trades = 0
        self.history = {}
        self.open_positions = {}

    def enter(self, type, instrument_token, date, price, strategy, strategycontext):
        # TODO: move this to the actual class
        if self.proxy:
            r = requests.post(
                self._url("/enter"),
                json={
                    "type": type,
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
            logging.info("Can't BUY trade with margin for the Stock {}".format(symbol))
            return

        # This logic should be updated by checking the actual amount and the leverage we can have self.margin_info[symbol]['leverage_margin']
        # self.quantity_tracker[symbol] = (
        #     int(5000 / price) if price < 5000 and self.ongoing_trades < 5 else 1
        # )
        self.quantity_tracker[symbol] = 1

        logging.info(
            "+Got Enter for {0} at date {1}".format(instrument_token, str(date))
        )

        send_message(
            "-Got Enter for {0} at date {2} Price={1}".format(symbol, price, str(date))
        )

        try:
            # TODO: Try placing a limit order instead of market order
            # Backtest with last 1 year of data to see if its profimaking idea.
            # order_id = self.kite.place_order(
            #     tradingsymbol=symbol,
            #     exchange=exchange,
            #     transaction_type=self.kite.TRANSACTION_TYPE_BUY,
            #     quantity=self.quantity_tracker[symbol],
            #     order_type=self.kite.ORDER_TYPE_MARKET,
            #     product=self.kite.PRODUCT_MIS,
            #     variety=self.kite.VARIETY_REGULAR,
            # )
            order_id = "RandomIdEnter"
            self.ongoing_trades = self.ongoing_trades + 1
            logging.info("Buy Order placed. ID is: {}".format(order_id))
            self.open_positions[symbol] = {
                "buy_price": price,
                "date": date,
                "execution_info": strategycontext,
                "strategy": strategy,
            }
        except:
            e = sys.exc_info()
            logging.info(
                "Error while placing the BUY Order for {0}".format(symbol), exc_info=e
            )
            send_message(
                "Error while placing the BUY Order for {0}\n with Exception : ".format(
                    symbol, str(e)
                )
            )

    def exit(self, type, instrument_token, date, price, strategy, strategycontext):
        import time

        if self.proxy:
            r = requests.post(
                self._url("/exit"),
                json={
                    "type": type,
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

        logging.info(
            "-Got Exit for {0} at date {1}".format(instrument_token, str(date))
        )

        send_message(
            "-Got Exit for {0} at date {2} Price={1}".format(symbol, price, str(date))
        )
        try:
            # order_id = self.kite.place_order(
            #     tradingsymbol=symbol,
            #     exchange=exchange,
            #     transaction_type=self.kite.TRANSACTION_TYPE_SELL,
            #     quantity=self.quantity_tracker[symbol],
            #     order_type=self.kite.ORDER_TYPE_MARKET,
            #     product=self.kite.PRODUCT_MIS,
            #     variety=self.kite.VARIETY_REGULAR,
            # )
            order_id = "RandomIdExit"
            logging.info("Sell Order placed. ID is: {}".format(order_id))
            open_position = self.open_positions.get(symbol)
            enter_date = open_position["date"]
            exit_date = date
            self.history.setdefault(symbol, []).append(
                {
                    "buy": open_position["buy_price"],
                    "sell": price,  # raw_trading_data[len(h) - 1]['close'],
                    "execution_info": open_position["execution_info"],
                    "entry_time": enter_date,
                    "exit_time": exit_date,
                }
            )

            self.open_positions["symbol"] = None
        except:
            e = sys.exc_info()
            logging.info(
                "Error while placing the SELL Order for {0}".format(symbol), exc_info=e
            )
            send_message(
                "Error while placing the SELL Order for {0}\n with Exception : ".format(
                    symbol, str(e)
                )
            )

    def summery(self):
        if not os.path.exists("./tmp/summery"):
            os.mkdir("./tmp/summery")
        file = open("./tmp/summery/history.json", "w")
        file.write(json.dumps(self.history, indent=1, default=str))
        file.close()
