import logging

from utils.objecthelpers import Singleton


class TradeBook(metaclass=Singleton):
    """TODO: Delete this class?"""

    def __init__(self):
        self.pl = {}
        self.summery_pl = []
        self.history = {}
        self.open_positions = {}
        """
            Single object map manupulation said to be not requiring locking in python            
        """
        self.trading_service = None

    def register_trading_service(self, trading_service):
        self.trading_service = trading_service

    def enter(
        self, trade_type, instrument_token, date, price, strategy, stragegy_context
    ):
        symbol, exchange = self.trading_service.get_symbol_and_exchange(
            instrument_token
        )

        logging.info(
            "BUY Time={0}, Stock={1} Price={2:5.2f}".format(str(date), symbol, price)
        )
        self.open_positions[symbol] = {
            "entry_price": price,
            "date": date,
            "execution_info": stragegy_context,
            "strategy": strategy,
        }

        if self.trading_service:
            self.trading_service.enter(
                trade_type, instrument_token, date, price, strategy, stragegy_context
            )

    def exit(
        self, trade_type, instrument_token, date, price, strategy, stragegy_context
    ):
        symbol, exchange = self.trading_service.get_symbol_and_exchange(
            instrument_token
        )
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
                "trade_type": trade_type,
            }
        )

        self.exit_line(symbol, price, price - open_position["entry_price"], date)

        """Close the open position"""
        self.open_positions[symbol] = None

        if self.trading_service:
            self.trading_service.exit(
                trade_type, instrument_token, date, price, strategy, stragegy_context
            )

    @staticmethod
    def exit_line(symbol, price, pl, transaction_date):
        logging.info(
            "SEL Time={0}, Stock={1} Price={2:5.2f}, PL={3:5.2f}".format(
                str(transaction_date), symbol, price, pl
            )
        )

    def get_previous_execution_info(self, instrument_token):
        symbol, exchange = self.trading_service.get_symbol_and_exchange(
            instrument_token
        )
        return self.open_positions.get(symbol)

    def summary(self):
        """
        This is dirty summery, formalize is better
        1) print stats such as Max Loss, Max Gain
        2) Continous loosing days
        3) Continous winning days
        4) DD - 100, -> 50, 150, 140  ~(150-140)/150
        """

        logging.info("-----------------Trendline Strategy Summary --------------")
        logging.info("Summary:" + str(self.history))

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
