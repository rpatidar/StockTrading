import logging

from db.storage import StorageHandler
from strategy.strategy import Strategy
from strategy.trend_detection.support_and_resistence_trend_detection import detect_trend


class TrendlineStrategy(Strategy):
    def __init__(self):

        super(TrendlineStrategy, self).__init__()
        self.scripts_bought = []
        self.tick_history = {}
        self.numbest = -1
        self.last_run = {}
        self.trend_following = {}
        self.flag = None
        """
            Store the data in following format 
            [
                { 
                    "date": "date(DD,MM,YY)",
                    "intraday_history": []
                }
            ]
        """
        self.agg_time = 5
        self.pending_trades = {}

        # self.last_closure = {}

    def close_day(self, date, instrument_token, backfill=False):
        if backfill:
            return
        self.pending_trades = {}
        self.trend_following = {}
        self.last_run[instrument_token] = -1
        # TODO: Fix the aggregate for the last minute, as of now the data is loaded for the previous candle, 5 minute aggregate before as
        # Current aggregate might be incomplete.
        sh = StorageHandler()
        data = self.get_trading_history_for_day(
            instrument_token, date.date(), False, agg_type=self.agg_time
        )
        if data is None:
            logging.info(
                "Received empty trading history data on "
                + str(date.date())
                + " for "
                + str(instrument_token)
            )
            return
        close_price = self.get_trading_history_for_day(
            instrument_token, date.date(), False, agg_type=self.agg_time
        )["trading_data"][-1]["close"]
        from db.tradebook import TradeBook

        tb = TradeBook()
        open_position = tb.get_previous_execution_info(instrument_token)
        if (
            open_position != None
            and open_position["execution_info"]["entry_ps"] != None
        ):
            pl = close_price - open_position["entry_price"]
            tb.exit("buy", instrument_token, date, close_price, "Trendline", None)

    def run(self, ticks, timestamp, backfill=False):
        for tick_data in ticks:
            instrument_token = tick_data["instrument_token"]
            trading_data = tick_data["ohlc"]
            date = timestamp.date()
            self._update_local_cache(tick_data, timestamp, agg_type=self.agg_time)
            if backfill:
                continue

            from db.tradebook import TradeBook

            tb = TradeBook()
            open_position_info = tb.get_previous_execution_info(instrument_token)
            h, raw_trading_data = self.get_simplified_trading_history(
                date, instrument_token
            )

            # TODO: this is little bit wrong, low is testing the condition is meet,
            # the order need to be placed.
            # Alternative is buy at the trade close price.
            if (
                self.pending_trades.get(instrument_token) != None
                # and self.pending_trades[instrument_token]['activation'] == False
                and tick_data["ohlc"]["low"]
                > self.pending_trades[instrument_token]["input_record"][3]
            ):
                parms = self.pending_trades[instrument_token]["input_record"]
                #                self.pending_trades[instrument_token]['activation'] = True
                # print("Entering the instrument at later stage to test the limit orders ")
                # tb.enter(*self.pending_trades[instrument_token]["input_record"])
                tb.enter(
                    parms[0],
                    parms[1],
                    timestamp,
                    tick_data["ohlc"]["close"],
                    parms[4],
                    parms[5],
                )
                self.pending_trades[instrument_token] = None
                continue

            # if (
            #     self.pending_trades.get(instrument_token) != None
            #     and self.pending_trades[instrument_token]['activation'] == True
            #     and tick_data["ohlc"]["low"] < self.pending_trades[instrument_token]["input_record"][3]
            # ):
            #     self.pending_trades[instrument_token]['activation'] = True
            #     # print("Entering the instrument at later stage to test the limit orders ")
            #     tb.enter(*self.pending_trades[instrument_token]["input_record"])
            #     self.pending_trades[instrument_token] = None
            #     return

            if open_position_info != None:

                exit_signal, stop_loss = self.check_for_exit_signal(
                    instrument_token, h, open_position_info, tick_data
                )
                # TODO: Close the position seprately irespective of tick data to avoid last movement closure
                three_fifteen = timestamp.replace(
                    hour=15, minute=15, second=0, microsecond=0
                )
                if exit_signal or timestamp > three_fifteen:
                    current_time = raw_trading_data[-1]["date"]
                    # StopLoss orders to hit at the buying price level.
                    exit_price = (
                        tick_data["ohlc"]["close"]
                        if timestamp > three_fifteen
                        else stop_loss
                    )

                    tb.exit(
                        "buy",
                        instrument_token,
                        current_time,  # Should we make it timestamp ?
                        exit_price,
                        # tick_data["ohlc"]["close"],
                        "Trendline",
                        None,
                    )
                    continue

            # If the aggregates are not updated should we run
            if len(h) <= self.last_run.get(instrument_token, 0):
                continue

            self.last_run[instrument_token] = len(h)

            # wait for enfough data points.
            if len(h) < 5:
                continue

            if timestamp > timestamp.replace(
                hour=15, minute=0, second=0, microsecond=0
            ):
                continue

            # This are the info before i forgot
            # 1. This gets called as soon as the last data point is completed.
            # 2. raw_trading_data[-1]['close']  points to the most recent data point.
            # logging.info(
            #     "Trying out on the following stock:"
            #     + str(instrument_token)
            #     + " timestamp:"
            #     + str(timestamp)
            #     + " len:"
            #     + str(len(h))
            #     + " price:"
            #     + str(h)
            # )
            # if instrument_token == 4818433:
            #     logging.debug("Raw trading data:" + str(raw_trading_data))

            #
            # This are the info before i forgot
            # 1. This gets called as soon as the last data point is completed.
            # 2. raw_trading_data[-1]['close']  points to the most recent data point.
            if (
                open_position_info == None
            ):  # or previous_strategy_execution_info['entry_ps'] == None:
                bug_signal, trend_info = self.execute_strategy_to_check_entry_signal(
                    h, raw_trading_data, tick_data, timestamp
                )
                if bug_signal:  # and two_pm_for_day > trade_time:
                    # Very Little bit of approximation  on the points,
                    # but a major in case if its across the days
                    # trade_data = raw_trading_data[-1]
                    # This will overwrite the entry signal
                    self.flag = instrument_token
                    self.pending_trades[instrument_token] = {
                        "input_record": (
                            "buy",
                            instrument_token,
                            tick_data["ohlc"]["date"],
                            tick_data["ohlc"]["close"] * 1.003,
                            "Trendline",
                            {"trend_info": trend_info, "entry_ps": len(h) - 1},
                        ),
                        "activation": False,
                    }

    def get_simplified_trading_history(self, date, instrument_token):
        """
        Looks mostly a hack, need to find if we it can be stored in simple format and pandas can be used to filter it out
        """
        raw0 = self.get_trading_history_for_day(
            instrument_token, date, False, agg_type=self.agg_time
        )
        raw1 = self.get_trading_history_for_day(
            instrument_token, date, True, agg_type=self.agg_time
        )
        raw_trading_data = raw1["trading_data"] if raw1 != None else []
        if raw0 != None:
            raw_trading_data = raw_trading_data + raw0["trading_data"]
        # As of now we are checking for 2 days only for trend detection, it can be increased to more data points
        # as we find more learnings.
        trading_history0 = self.holc_to(raw0, "low")
        trading_history1 = self.holc_to(raw1, "low")
        current_aggregate = []
        if trading_history1 != None:
            current_aggregate = current_aggregate + trading_history1
        if trading_history0 != None:
            current_aggregate = current_aggregate + trading_history0
        h = current_aggregate
        return h, raw_trading_data

    def check_for_exit_signal(self, instrument_token, h, open_position_info, tick_data):
        trend_info = open_position_info["execution_info"]["trend_info"]
        # Detect the stop loss based on the trend line and also keep a margin of .5 percent below trendline.
        """worst case Stop loss could be any percentage may be more than 
        0.5 or 1% as its calculated mathamatically and buying could happen above the trend line """
        stop_loss = (len(h)) * (trend_info["slope"]) + trend_info["coefficient"]
        stop_loss = 0.985 * stop_loss
        # Change to low to make or change logic based on 1 minute candle
        exit_signal = stop_loss > tick_data["ohlc"]["close"]

        # Lets not sell if the loss is not high,
        # very critical in avoiding unnecessary losses.
        # TODO: validate adding a Stop Loss on maximum loss can be incurred and run backtest for a 1 year
        current_pl = (
            (tick_data["ohlc"]["close"] - open_position_info["entry_price"])
            / open_position_info["entry_price"]
        ) * 100

        # Change the Sell Signal to false.
        if exit_signal and -1.5 < current_pl:
            return False, stop_loss

        if self.trend_following.get(instrument_token):
            sl = self.trend_following[instrument_token]["stop_loss"]
            if sl < tick_data["ohlc"]["high"]:
                self.trend_following[instrument_token] = None
                return True, sl

        # Worst case condition it was never hit Changed from < to >,
        if -2 > current_pl:
            return (
                True,
                tick_data["ohlc"]["close"],
            )  # open_position_info["entry_price"] * 0.980
        # Current PL changed < to >
        if -1.5 > current_pl:
            self.trend_following[instrument_token] = {
                "stop_loss": open_position_info["entry_price"] * 0.990
            }
        return exit_signal, stop_loss

    def execute_strategy_to_check_entry_signal(
        self, h, raw_trading_data, tick_data, timestamp
    ):
        """
        minwindows values return following format : [],(X,X,X,X,X,X)
        (1) Array of Trend points -
        (2) Touple of following values
            (1) -- Slope,
            (2) -- Coefficient/Regression Intercept,
            (3) -- ys=Sum of squre residual for the expected Y
            (4) -- ser = Standard Error of Slope
            (5) -- SigmaM=Standard Error of Intercept
            (6) -- Sum of Area because of error gaps
        """
        mintrend, minwindows = detect_trend(h)
        trend_info = {}
        bug_signal = False
        for trends in minwindows:
            best_trend = None
            for trend in trends:

                # Total percentage changes in the Slope (from the starting to end )
                percentage_change = ((h[-1] - h[trend[0][0]]) / h[trend[0][0]]) * 100

                # Based on the trend how many percentage is changed per data point in the trned?
                percentage_change_per_data_points = percentage_change / (
                    trend[0][-1] - trend[0][0]
                )

                # ?
                error_slope_pct = (trend[1][3] / h[trend[0][0]]) * 100

                # Convert the slop in terms of actual count to the percentage so its remain
                # same for all stocks
                slope_percentage = (trend[1][0] / h[trend[0][0]]) * 100

                # Magic number derived based on trial and error
                if (
                    percentage_change_per_data_points > 0.080
                    and slope_percentage > 0.080
                ):

                    # Find the best Slope if there are multiple meeting the condition.
                    if trend_info.get("slope") == None or (
                        trend_info.get("slope") != None
                        and trend_info.get("slope") < trend[1][0]
                    ):
                        temp_closing_index = trend[0][-1]

                        # Only use this trend if the trend is closing on the last data point.
                        if (len(h) - 1 - temp_closing_index) == 0:
                            # Book keeping information on why we bought it here
                            trend_info["trendpoints"] = [
                                {
                                    "price": raw_trading_data[i]["low"],
                                    "date": raw_trading_data[i]["date"].timestamp(),
                                }
                                for i in trend[0]
                            ]
                            # Y=MX+B
                            # Current Slope (M)
                            trend_info["slope"] = trend[1][0]
                            # Intercept(B)
                            trend_info["coefficient"] = trend[1][1]
                            gap_percentage = 100 * (
                                (
                                    tick_data["ohlc"]["close"]
                                    - (
                                        (len(h) - 1) * (trend_info["slope"])
                                        + trend_info["coefficient"]
                                    )
                                )
                                / h[-1]
                            )
                            bug_signal = gap_percentage < 0.4 and gap_percentage > -0.4
                            logging.info(("H=" + str(h)))
                            logging.info("EntrySignal : " + str(bug_signal))

        return bug_signal, trend_info
