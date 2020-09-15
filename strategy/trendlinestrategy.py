import numpy as np

from strategy.strategy import Strategy
import datetime

import db.storage

import copy

import os
import matplotlib
import matplotlib.pyplot as plt
import threading

class TrendlineStrategy(Strategy):

    def __init__(self):

        super(TrendlineStrategy, self).__init__()
        self.pl = {}
        self.summery_pl = []
        self.scripts_bought = []
        self.tick_history = {}
        from findiff import FinDiff
        self.accuracy = 1
        dx = 1  # 1 day interval
        self.d_dx = FinDiff(0, dx, 1, acc=self.accuracy)  # acc=3 #for 5-point stencil, currenly uses +/-1 day only
        self.d2_dx2 = FinDiff(0, dx, 2, acc=self.accuracy)  # acc=3 #for 5-point stencil, currenly uses +/-1 day only
        self.numbest = -1
        self.pctbound = 1
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
        self.buy_sell_lock = threading.Lock()
        #self.last_closure = {}

    def summary(self):
        print("-----------------Trendline Strategy Summary --------------")
        print("Summary:" + str(self.pl))
        import json
        print("Debug Info: ------")
        if not os.path.exists("./tmp/summery"):
            os.mkdir("./tmp/summery")

        file = open("./tmp/summery/trendline0.json", "w")
        file.write(json.dumps(db.storage.get_st_context(), indent=1, default=str))
        file.close()
        file = open("./tmp/summery/trendline1.json", "w")
        file.write(json.dumps(self.summery_pl, indent=1, default=str))
        file.close()
        file = open("./tmp/summery/trendline2.json", "w")
        file.write(json.dumps(self.pl, indent=1, default=str))
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

    def close_day(self, date, instrument_token):
        self.last_run[instrument_token] = -1
        #TODO: Fix the aggregate for the last minute, as of now the data is loaded for the previous candle, 5 minute aggregate before as
        #Current aggregate might be incomplete.
        close_price = self.get_trading_history_for_day(instrument_token, date.date(), False, agg_type=self.agg_time)["trading_data"][-1]['close']
        previous_strategy_execution_info = db.storage.get_st_context().get(instrument_token)
        if previous_strategy_execution_info != None and previous_strategy_execution_info['buy_ps'] != None:
            pl = close_price - previous_strategy_execution_info['buy_price']
            self.sell_line(close_price, pl, date)
            self.update_pl_summery(previous_strategy_execution_info['buy_price'], instrument_token, pl)
            previous_strategy_execution_info['buy_ps'] = None

    def run(self, tick_datas, riskmanagement, timestamp):
        for tick_data in tick_datas:
            instrument_token = tick_data['instrument_token']
            trading_data = tick_data['ohlc']
            date = timestamp.date();
            self._update_local_cache(tick_data, timestamp, agg_type=self.agg_time)
            h, raw_trading_data = self.get_simplified_trading_history(date, instrument_token)

            #If the aggregates are not updated should we run
            if len(h) <= self.last_run.get(instrument_token, 0):
                return

            self.last_run[instrument_token] = len(h)
            if (len(h) > 5):
                previous_strategy_execution_info = self.get_previous_execution_info(instrument_token)
                if previous_strategy_execution_info['buy_ps'] == None:
                    bug_signal, trend_info = self.execute_strategy_to_check_buy_signal(h, raw_trading_data)
                    if bug_signal :  # and two_pm_for_day > trade_time:
                        self.buy_sell_lock.acquire()
                        trade_data = raw_trading_data[-1]
                        print(("BUY Time={0}, Price={1:5.2f}").format(str(trade_data['date']), h[-1]))
                        previous_strategy_execution_info['trend_info'] = trend_info
                        previous_strategy_execution_info['buy_ps'] = len(h) - 1
                        previous_strategy_execution_info['buy_price'] = trade_data['close']
                        self.buy_sell_lock.release()
                else:
                    sell_signal, stop_loss = self.check_for_sell_signal(h, previous_strategy_execution_info)
                    if sell_signal:
                        self.buy_sell_lock.acquire()
                        buy_ps = h[previous_strategy_execution_info['buy_ps']]
                        pl = stop_loss - h[previous_strategy_execution_info['buy_ps']]
                        current_time  = raw_trading_data[-1]['date']
                        self.sell_line(stop_loss, pl, current_time)
                        previous_strategy_execution_info['history'].append(
                            {"buy": buy_ps,
                             "sell": stop_loss, # raw_trading_data[len(h) - 1]['close'],
                             "trend_info": previous_strategy_execution_info["trend_info"]})
                        previous_strategy_execution_info["buy_ps"] = None
                        previous_strategy_execution_info["trend_info"] = None
                        self.update_pl_summery(buy_ps, instrument_token, pl)
                        self.buy_sell_lock.release()


    def get_simplified_trading_history(self, date, instrument_token):
        raw0 = self.get_trading_history_for_day(instrument_token, date, False, agg_type=self.agg_time)
        raw1 = self.get_trading_history_for_day(instrument_token, date, True, agg_type=self.agg_time)
        raw_trading_data = raw1['trading_data'] if raw1 != None else []
        if raw0 != None:
            raw_trading_data = raw_trading_data + raw0['trading_data']
        trading_history0 = self.to_close(raw0)
        trading_history1 = self.to_close(raw1)
        current_aggregate = []
        if trading_history1 != None:
            current_aggregate = current_aggregate + trading_history1
        if trading_history0 != None:
            current_aggregate = current_aggregate + trading_history0
        h = current_aggregate
        return h, raw_trading_data

    def check_for_sell_signal(self, h, previous_strategy_execution_info):
        trend_info = previous_strategy_execution_info['trend_info']
        stop_loss = (len(h) - 1) * (trend_info['slope']) + trend_info['coefficient']
        stop_loss = 0.995 * stop_loss
        sell_signal = stop_loss > h[-1]
        return sell_signal, stop_loss

    def execute_strategy_to_check_buy_signal(self, h, raw_trading_data):
        mintrend, minwindows = self.detect_trend(h)
        trend_info = {}
        for trends in minwindows:
            for trend in trends:
                percentage_change = (trend[1][0] / h[-1]) * 100
                if (percentage_change > 0.10 and trend_info.get("slope") == None) or (
                        trend_info.get("slope") != None and trend_info.get("slope") < trend[1][0]):
                    temp_closing_index = trend[0][-1]
                    if temp_closing_index == len(h) - 3:
                        # Record the current trend line info
                        trend_info["trendpoints"] = [
                            {"price": raw_trading_data[i]['low'], "date": raw_trading_data[i]['date']} for
                            i in trend[0]]
                        trend_info["slope"] = trend[1][0]
                        trend_info['coefficient'] = trend[1][1]
        bug_signal = trend_info.get('slope') != None and h[-2] > (len(h) - 2) * (trend_info['slope']) + trend_info[
            'coefficient']
        return bug_signal, trend_info

    def get_previous_execution_info(self, instrument_token):
        previous_strategy_execution_info = db.storage.get_st_context().setdefault(instrument_token, {
            "buy_ps": None,
            "history": []
        })
        return previous_strategy_execution_info

    def update_pl_summery(self, buy_ps, instrument_token, pl):
        pl_record = self.pl.get(instrument_token)
        if pl_record == None:
            pl_record = {"pl": 0, "change": 0}
        pl_record['pl'] = pl_record['pl'] + pl
        change = (pl / buy_ps ) * 100
        pl_record['change'] = pl_record['change'] + change
        self.pl[instrument_token] = pl_record
        self.summery_pl.append({"instrument_token": instrument_token, "pl-percentage": change})

    def sell_line(self, price, pl, transaction_date):
        print(("SEL Time={0}, Price={1:5.2f}, PL={2:5.2f}").format(str(transaction_date), price, pl))

    def detect_trend(self, h, window=40, errpct=10):
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

        def measure_area(trendline, isMin, h):  # Reimann sum of line to discrete time series data
            # first determine the time range, and subtract the line values to obtain a single function
            # support subtracts the line minus the series and eliminates the negative values
            # resistances subtracts the series minus the line and eliminate the negatives
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
