import logging
import os
import threading

from db.storage import StorageHandler
from utils.objecthelpers import Singleton


class TradeBook(metaclass=Singleton):

    def __init__(self):
        self.pl = {}
        self.summery_pl = []
        self.history = {}
        self.open_positions = {}
        """
            Single object map manupulation said to be not requiring locking in python            
        """
        self.buy_sell_lock = threading.Lock()
        self.trading_service = None

    def register_trading_service(self, trading_service):
        self.trading_service = trading_service

    def enter(self, type, instrument_token, date, price, strategy, stragegy_context):
        self.buy_sell_lock.acquire()

        logging.info(("BUY Time={0}, Price={1:5.2f}").format(str(date), price))
        self.open_positions[instrument_token] = {
            "buy_price": price,
            "date": date,
            "execution_info": stragegy_context,
            "strategy": strategy
        }

        if self.trading_service:
            self.trading_service.enter(type, instrument_token, date, price, strategy)

        self.buy_sell_lock.release()

    def exit(self, type, instrument_token, date, price, strategy, stragegy_context):
        self.buy_sell_lock.acquire()
        sh = StorageHandler()
        open_position = self.open_positions.get(instrument_token)
        self.history.setdefault(instrument_token, []).append(
            {"buy": open_position['buy_price'],
             "sell": price,  # raw_trading_data[len(h) - 1]['close'],
             "execution_info": open_position["execution_info"]})

        """TODO: Find better way to combine this into one place"""
        self.update_pl_summery(open_position['buy_price'], instrument_token, price - open_position['buy_price'])
        self.sell_line(price, price - open_position['buy_price'], date)

        """Close the open position"""
        self.open_positions[instrument_token] = None

        if self.trading_service:
            self.trading_service.exit(type, instrument_token, date, price, strategy)

        self.buy_sell_lock.release()

    def update_pl_summery(self, buy_ps, instrument_token, pl):
        pl_record = self.pl.get(instrument_token)
        if pl_record == None:
            pl_record = {"pl": 0, "change": 0}
        pl_record['pl'] = pl_record['pl'] + pl
        change = (pl / buy_ps) * 100
        pl_record['change'] = pl_record['change'] + change
        self.pl[instrument_token] = pl_record
        self.summery_pl.append({"instrument_token": instrument_token, "pl-percentage": change})

    def sell_line(self, price, pl, transaction_date):
        logging.info(("SEL Time={0}, Price={1:5.2f}, PL={2:5.2f}").format(str(transaction_date), price, pl))

    def get_previous_execution_info(self, instrument_token):
        return self.open_positions.get(instrument_token)

    def summary(self):
        sh = StorageHandler()
        """
            This is dirty summery, formalize is better
            1) print stats such as Max Loss, Max Gain
            2) Continous loosing days
            3) Continous winning days
            4) DD - 100, -> 50, 150, 140  ~(150-140)/150            
        """

        logging.info("-----------------Trendline Strategy Summary --------------")
        logging.info("Summary:" + str(self.pl))
        import json
        logging.info("Debug Info: ------")
        if not os.path.exists("./tmp/summery"):
            os.mkdir("./tmp/summery")

        # file = open("./tmp/summery/trendline0.json", "w")
        #
        # file.write(json.dumps(sh.get_st_context(), indent=1, default=str))
        # file.close()
        file = open("./tmp/summery/trendline1.json", "w")
        file.write(json.dumps(self.summery_pl, indent=1, default=str))
        file.close()
        file = open("./tmp/summery/trendline2.json", "w")
        file.write(json.dumps(self.pl, indent=1, default=str))
        file.close()
        file = open("./tmp/summery/history.json", "w")
        file.write(json.dumps(self.history, indent=1, default=str))
        file.close()
        # TODO: for debugging the graphs
        # intresting_instrument_token = 738561
        # instresing_dates = []
        # db.storage.get_db()
        # aggregate1 = self.get_trading_history_for_day(intresting_instrument_token, datetime.datetime(2020, 8, 5).date(), False, agg_type=self.agg_time)
        # aggregate2 = self.get_trading_history_for_day(intresting_instrument_token, datetime.datetime(2020, 8, 5).date(), True, agg_type=self.agg_time)
        # final_data = []
        # if aggregate2 != None:
        #     final_data = final_data + self.to_close(aggregate2)
        # if aggregate1 != None:
        #     final_data = final_data + self.to_close(aggregate1)
        # final_dates = []
        # if aggregate2 != None:
        #     final_dates = final_dates + self.to_date(aggregate2)
        # if aggregate1 != None:
        #     final_dates = final_dates + self.to_date(aggregate1)
        #
        #
        # fig = plt.figure(figsize = (18,8))
        # plt.subplot(1,1,1)
        # plt.scatter([f'{x:%Y-%m-%d %H:%M}' for x in final_dates], final_data)
        # plt.show()


pass
