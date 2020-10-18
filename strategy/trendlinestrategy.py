import logging

import numpy as np

from db.storage import StorageHandler
from strategy.strategy import Strategy


class TrendlineStrategy(Strategy):

    def __init__(self):

        super(TrendlineStrategy, self).__init__()
        self.scripts_bought = []
        self.tick_history = {}
        from findiff import FinDiff
        self.accuracy = 1
        dx = 1  # 1 day interval
        self.d_dx = FinDiff(0, dx, 1, acc=self.accuracy)  # acc=3 #for 5-point stencil, currenly uses +/-1 day only
        self.d2_dx2 = FinDiff(0, dx, 2, acc=self.accuracy)  # acc=3 #for 5-point stencil, currenly uses +/-1 day only
        self.numbest = -1
        self.pctbound = 0.20
        self.last_run = {}
        """
            Store the data in following format 
            [
                { 
                    "date": "date(DD,MM,YY)",
                    "intraday_history": []
                }
            ]
        """
        self.market_history = {}
        self.agg_time = 5

        # self.last_closure = {}

    def close_day(self, date, instrument_token, backfill=False):
        if backfill:
            return

        self.last_run[instrument_token] = -1
        # TODO: Fix the aggregate for the last minute, as of now the data is loaded for the previous candle, 5 minute aggregate before as
        # Current aggregate might be incomplete.
        sh = StorageHandler()
        data = self.get_trading_history_for_day(instrument_token, date.date(), False, agg_type=self.agg_time)
        if data is None:
            logging.info("Received empty trading history data on " + str(date.date()) + " for " + str(instrument_token))
            return
        close_price = \
            self.get_trading_history_for_day(instrument_token, date.date(), False, agg_type=self.agg_time)[
                "trading_data"][
                -1]['close']
        from db.tradebook import TradeBook
        tb = TradeBook()
        open_position = tb.get_previous_execution_info(instrument_token)
        if open_position != None and open_position['execution_info']['buy_ps'] != None:
            pl = close_price - open_position['buy_price']
            tb.exit("buy", instrument_token, date, close_price, "Trendline", None)

    def run(self, tick_datas, riskmanagement, timestamp, backfill=False):
        for tick_data in tick_datas:
            instrument_token = tick_data['instrument_token']
            trading_data = tick_data['ohlc']
            date = timestamp.date();
            self._update_local_cache(tick_data, timestamp, agg_type=self.agg_time)
            if backfill:
                continue

            from db.tradebook import TradeBook
            tb = TradeBook()
            open_position_info = tb.get_previous_execution_info(instrument_token)
            h, raw_trading_data = self.get_simplified_trading_history(date, instrument_token)

            if open_position_info != None:
                sell_signal, stop_loss = self.check_for_sell_signal(h, open_position_info, tick_data)
                three_fifteen = timestamp.replace(hour=15, minute=15, second=0, microsecond=0)
                if sell_signal or timestamp > three_fifteen:
                    current_time = raw_trading_data[-1]['date']
                    tb.exit("buy", instrument_token, current_time, stop_loss, "Trendline", None)
                    return

            # If the aggregates are not updated should we run
            if len(h) <= self.last_run.get(instrument_token, 0):
                return

            self.last_run[instrument_token] = len(h)

            # wait for enfough data points.
            if (len(h) < 5):
                return

            if timestamp > timestamp.replace(hour=15, minute=0, second=0, microsecond=0):
                return

            # This are the info before i forgot
            # 1. This gets called as soon as the last data point is completed.
            # 2. raw_trading_data[-1]['close']  points to the most recent data point.
            logging.info("Trying out on the following stock:" + str(instrument_token) + " timestamp:" + str(
                timestamp) + " len:" + str(len(h)) + " price:" + str(h))
            if instrument_token == 4818433:
                logging.debug("Raw trading data:" + str(raw_trading_data))

            #
            # This are the info before i forgot
            # 1. This gets called as soon as the last data point is completed.
            # 2. raw_trading_data[-1]['close']  points to the most recent data point.
            if open_position_info == None:  # or previous_strategy_execution_info['buy_ps'] == None:
                bug_signal, trend_info = self.execute_strategy_to_check_buy_signal(h, raw_trading_data, tick_data,
                                                                                   timestamp)
                if bug_signal:  # and two_pm_for_day > trade_time:
                    # Very Little bit of approximation  on the points,
                    # but a major in case if its across the days
                    # trade_data = raw_trading_data[-1]
                    tb.enter("buy", instrument_token, tick_data['ohlc']['date'], tick_data['ohlc']['close'],
                             "Trendline",
                             {"trend_info": trend_info, "buy_ps": len(h) - 1})

    def get_simplified_trading_history(self, date, instrument_token):
        """
        Looks mostly a hack, need to find if we it can be stored in simple format and pandas can be used to filter it out
        """
        raw0 = self.get_trading_history_for_day(instrument_token, date, False, agg_type=self.agg_time)
        raw1 = self.get_trading_history_for_day(instrument_token, date, True, agg_type=self.agg_time)
        raw_trading_data = raw1['trading_data'] if raw1 != None else []
        if raw0 != None:
            raw_trading_data = raw_trading_data + raw0['trading_data']
        # As of now we are checking for 2 days only for trend detection, it can be increased to more data points
        # as we find more learnings.
        trading_history0 = self.holc_to(raw0, 'low')
        trading_history1 = self.holc_to(raw1, 'low')
        current_aggregate = []
        if trading_history1 != None:
            current_aggregate = current_aggregate + trading_history1
        if trading_history0 != None:
            current_aggregate = current_aggregate + trading_history0
        h = current_aggregate
        return h, raw_trading_data

    def check_for_sell_signal(self, h, open_position_info, tick_data):
        trend_info = open_position_info['execution_info']['trend_info']
        # Detect the stop loss based on the trend line and also keep a margin of .5 percent below trendline.
        stop_loss = (len(h)) * (trend_info['slope']) + trend_info['coefficient']
        stop_loss = 0.995 * stop_loss
        sell_signal = stop_loss > tick_data['ohlc']['close']

        # Not enough evidence of this helping but sounds better
        if not sell_signal:
            # TODO: Run permutation on what is the best max profit to book.
            if (((tick_data['ohlc']['close'] - open_position_info['buy_price']) / open_position_info[
                'buy_price']) * 100) > 3:
                return True, h[-1]

        # Lets not sell if the loss is not high,
        # very critical in avoiding unnecessary losses.
        if sell_signal and (((tick_data['ohlc']['close'] - open_position_info['buy_price']) / open_position_info[
            'buy_price']) * 100) < 0.5:
            return False, stop_loss
        return sell_signal, stop_loss

    def execute_strategy_to_check_buy_signal(self, h, raw_trading_data, tick_data, timestamp):
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
        mintrend, minwindows = self.detect_trend(h)
        trend_info = {}
        bug_signal = False
        for trends in minwindows:
            best_trend = None
            for trend in trends:

                # Total percentage changes in the Slope (from the starting to end )
                percentage_change = ((h[-1] - h[trend[0][0]]) / h[trend[0][0]]) * 100

                # Based on the trend how many percentage is changed per data point in the trned?
                percentage_change_per_data_points = percentage_change / (trend[0][-1] - trend[0][0])

                # ?
                error_slope_pct = (trend[1][3] / h[trend[0][0]]) * 100

                # Convert the slop in terms of actual count to the percentage so its remain
                # same for all stocks
                slope_percentage = (trend[1][0] / h[trend[0][0]]) * 100

                # Magic number derived based on trial and error
                if (percentage_change_per_data_points > 0.080 and slope_percentage > 0.080):

                    # Find the best Slope if there are multiple meeting the condition.
                    if trend_info.get("slope") == None or (
                            trend_info.get("slope") != None and trend_info.get("slope") < trend[1][0]):
                        temp_closing_index = trend[0][-1]

                        # Only use this trend if the trend is closing on the last data point.
                        if (len(h) - 1 - temp_closing_index) == 0:
                            # Book keeping information on why we bought it here
                            trend_info["trendpoints"] = [
                                {"price": raw_trading_data[i]['low'], "date": raw_trading_data[i]['date']} for i in
                                trend[0]]
                            # Y=MX+B
                            # Current Slope (M)
                            trend_info["slope"] = trend[1][0]
                            # Intercept(B)
                            trend_info['coefficient'] = trend[1][1]
                            gap_percentage = (100 * (
                                    (tick_data['ohlc']['close'] - (
                                            (len(h) - 1) * (trend_info['slope']) + trend_info['coefficient'])) /
                                    h[-1]))
                            bug_signal = gap_percentage < 0.4 and gap_percentage > -0.4

                            logging.info("BuySignal : " + str(bug_signal))

        return bug_signal, trend_info

    def detect_trend(self, h, window=30, errpct=1):
        """
            Actual trend line detection code
            Extracted the code from: https://github.com/GregoryMorse/trendln
        """
        len_h = len(h)
        min_h, max_h = min(h), max(h)

        def merge_lines(Idxs, trend, h, fltpct):
            for x in Idxs:
                l = []
                for i, (p, r) in enumerate(trend):
                    if x in p: l.append((r[0], i))
                l.sort()  # key=lambda val: val[0])
                if len(l) > 1: CurIdxs = list(trend[l[0][1]][0])
                for (s, i) in l[1:]:
                    CurIdxs += trend[i][0]
                    CurIdxs = list(dict.fromkeys(CurIdxs))
                    CurIdxs.sort()
                    res = get_bestfit([(p, h[p]) for p in CurIdxs])
                    if res[3] <= fltpct:
                        trend[i - 1], trend[i], CurIdxs = ([], None), (CurIdxs, res), list(CurIdxs)
                    else:
                        CurIdxs = list(trend[i][0])  # restart search from here
            return list(filter(lambda val: val[0] != [], trend))

        def measure_area(trendline, isMin, h):
            """
            Reimann sum of line to discrete time series data
            first determine the time range, and subtract the line values to obtain a single function
            support subtracts the line minus the series and eliminates the negative values
            resistances subtracts the series minus the line and eliminate the negatives
            """
            base = trendline[0][0]
            m, b, ser = trendline[1][0], trendline[1][1], h[base:trendline[0][-1] + 1]
            return sum([max(0, (m * (x + base) + b) - y if isMin else y - (m * (x + base) + b)) for x, y in
                        enumerate(ser)]) / len(ser)

        def window_results(trends, isMin, h):
            windows = [[] for x in range(len(divide) - 1)]
            for x in trends:
                fstwin, lastwin = int(x[0][0] / window), int(x[0][-1] / window)
                wins = [[] for _ in range(fstwin, lastwin + 1)]
                for y in x[0]: wins[int(y / window) - fstwin].append(y)
                for y in range(0, lastwin - fstwin):
                    if len(wins[y + 1]) == 0 and len(wins[y]) >= 3: windows[fstwin + y].append(wins[y])
                    if len(wins[y]) + len(wins[y + 1]) >= 3:
                        windows[fstwin + y + 1].append(wins[y] + wins[y + 1])
                if lastwin - fstwin == 0 and len(wins[0]) >= 3: windows[fstwin].append(wins[0])

            def fitarea(x):
                fit = get_bestfit([(y, h[y]) for y in x])
                return (x, fit + (measure_area((x, fit), isMin, h),))

            def dosort(x):
                x.sort(key=lambda val: val[1][skey])
                return x

            return [dosort(list(fitarea(pts) for pts in x)) for x in windows]

        def get_bestfit(pts):
            xbar, ybar = [sum(x) / len(x) for x in zip(*pts)]

            def subcalc(x, y):
                tx, ty = x - xbar, y - ybar
                return tx * ty, tx * tx, x * x

            (xy, xs, xx) = [sum(q) for q in zip(*[subcalc(x, y) for x, y in pts])]
            m = xy / xs
            b = ybar - m * xbar
            ys = sum([np.square(y - (m * x + b)) for x, y in pts])
            ser = np.sqrt(ys / ((len(pts) - 2) * xs))
            return m, b, ys, ser, ser * np.sqrt(xx / len(pts))

        def trendmethod(Idxs, h, fltpct, min_h, max_h):
            slopes, trend = [], []
            for x in range(len(Idxs)):  # O(n^2*log n) algorithm
                slopes.append([])
                for y in range(x + 1, len(Idxs)):
                    slope = (h[Idxs[x]] - h[Idxs[y]]) / (Idxs[x] - Idxs[
                        y])  # m=dy/dx #if slope 0 then intercept does not exist constant y where y=b
                    # intercept = h[Idxs[x]] - slope * Idxs[x] #y=mx+b, b=y-mx
                    slopes[x].append((slope, y))
            for x in range(len(Idxs)):
                slopes[x].sort()  # key=lambda val: val[0])
                CurIdxs = [Idxs[x]]
                for y in range(0, len(slopes[x])):
                    # distance = abs(slopes[x][y][2] * slopes[x][y+1][1] + slopes[x][y][3] - h[slopes[x][y+1][1]])
                    CurIdxs.append(Idxs[slopes[x][y][1]])
                    if len(CurIdxs) < 3: continue
                    res = get_bestfit([(p, h[p]) for p in CurIdxs])
                    if res[3] <= fltpct:
                        CurIdxs.sort()
                        if len(CurIdxs) == 3:
                            trend.append((CurIdxs, res))
                            CurIdxs = list(CurIdxs)
                        else:
                            CurIdxs, trend[-1] = list(CurIdxs), (CurIdxs, res)
                        # if len(CurIdxs) >= MaxPts: CurIdxs = [CurIdxs[0], CurIdxs[-1]]
                    else:
                        CurIdxs = [CurIdxs[0], CurIdxs[-1]]  # restart search from this point
            return trend

        def calc_all(idxs, h, isMin):
            min_h, max_h = min(h), max(h)
            scale = (max_h - min_h) / len_h
            fltpct = scale * errpct
            midxs = [[] for _ in range(len(divide) - 1)]
            for x in idxs:
                midxs[int((x + rem) / window)].append(x)
            mtrend = []
            for x in range(len(divide) - 1 - 1):
                m = midxs[x] + midxs[x + 1]
                mtrend.extend(trendmethod(m, h, fltpct, min_h, max_h))
            if len(divide) == 2:
                mtrend.extend(trendmethod(midxs[0], h, fltpct, min_h, max_h))
            mtrend = merge_lines(idxs, mtrend, h, fltpct)
            mtrend = [(pts, (res[0], res[1], res[2], res[3], res[4], measure_area((pts, res), isMin, h))) for
                      pts, res in
                      mtrend]
            mtrend.sort(key=lambda val: val[1][skey])
            mwindows = window_results(mtrend, isMin, h)
            # pm = overall_line(idxs, [h[x] for x in idxs])
            # print((pmin, pmax, zmne, zmxe))
            return mtrend, mwindows

        def get_extrema(h, accuracy=1):
            hmin, hmax = None, None
            # pip install findiff
            from findiff import FinDiff
            dx = 1  # 1 day interval
            d_dx = FinDiff(0, dx, 1, acc=accuracy)  # acc=3 #for 5-point stencil, currenly uses +/-1 day only
            d2_dx2 = FinDiff(0, dx, 2, acc=accuracy)  # acc=3 #for 5-point stencil, currenly uses +/-1 day only

            def get_minmax(h):
                clarr = np.asarray(h, dtype=np.float64)
                mom, momacc = d_dx(clarr), d2_dx2(clarr)

                # print(mom[-10:], momacc[-10:])
                # numerical derivative will yield prominent extrema points only
                def numdiff_extrema(func):
                    return [x for x in range(len(mom))
                            if func(x) and
                            (mom[
                                 x] == 0 or  # either slope is 0, or it crosses from positive to negative with the closer to 0 of the two chosen or prior if a tie
                             (x != len(mom) - 1 and (mom[x] > 0 and mom[x + 1] < 0 and h[x] >= h[
                                 x + 1] or  # mom[x] >= -mom[x+1]
                                                     mom[x] < 0 and mom[x + 1] > 0 and h[x] <= h[
                                                         x + 1]) or  # -mom[x] >= mom[x+1]) or
                              x != 0 and (mom[x - 1] > 0 and mom[x] < 0 and h[x - 1] < h[
                                         x] or  # mom[x-1] < -mom[x] or
                                          mom[x - 1] < 0 and mom[x] > 0 and h[x - 1] > h[
                                              x])))]  # -mom[x-1] < mom[x])))]

                return lambda x: momacc[x] > 0, lambda x: momacc[x] < 0, numdiff_extrema

            minFunc, maxFunc, numdiff_extrema = get_minmax(h)
            return numdiff_extrema(minFunc), numdiff_extrema(maxFunc)

        divide = list(reversed(range(len_h, -window, -window)))
        rem, divide[0] = window - len_h % window, 0
        if rem == window: rem = 0
        skey = 5  # if sortError else 5
        extremaIdxs = get_extrema(h, self.accuracy)
        mintrend, minwindows = calc_all(extremaIdxs[0], h, True)
        return mintrend, minwindows
