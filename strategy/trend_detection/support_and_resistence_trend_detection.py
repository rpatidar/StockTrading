import numpy as np
from findiff import FinDiff

accuracy = 1
dx = 1  # 1 day interval
d_dx = FinDiff(
    0, dx, 1, acc=accuracy
)  # acc=3 #for 5-point stencil, currenly uses +/-1 day only
d2_dx2 = FinDiff(
    0, dx, 2, acc=accuracy
)  # acc=3 #for 5-point stencil, currenly uses +/-1 day only


def detect_trend(h, window=30, errpct=1):
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
                if x in p:
                    l.append((r[0], i))
            l.sort()  # key=lambda val: val[0])
            if len(l) > 1:
                CurIdxs = list(trend[l[0][1]][0])
            for (s, i) in l[1:]:
                CurIdxs += trend[i][0]
                CurIdxs = list(dict.fromkeys(CurIdxs))
                CurIdxs.sort()
                res = get_bestfit([(p, h[p]) for p in CurIdxs])
                if res[3] <= fltpct:
                    trend[i - 1], trend[i], CurIdxs = (
                        ([], None),
                        (CurIdxs, res),
                        list(CurIdxs),
                    )
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
        m, b, ser = trendline[1][0], trendline[1][1], h[base : trendline[0][-1] + 1]
        return sum(
            [
                max(0, (m * (x + base) + b) - y if isMin else y - (m * (x + base) + b))
                for x, y in enumerate(ser)
            ]
        ) / len(ser)

    def window_results(trends, isMin, h):
        windows = [[] for x in range(len(divide) - 1)]
        for x in trends:
            fstwin, lastwin = int(x[0][0] / window), int(x[0][-1] / window)
            wins = [[] for _ in range(fstwin, lastwin + 1)]
            for y in x[0]:
                wins[int(y / window) - fstwin].append(y)
            for y in range(0, lastwin - fstwin):
                if len(wins[y + 1]) == 0 and len(wins[y]) >= 3:
                    windows[fstwin + y].append(wins[y])
                if len(wins[y]) + len(wins[y + 1]) >= 3:
                    windows[fstwin + y + 1].append(wins[y] + wins[y + 1])
            if lastwin - fstwin == 0 and len(wins[0]) >= 3:
                windows[fstwin].append(wins[0])

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
                slope = (h[Idxs[x]] - h[Idxs[y]]) / (
                    Idxs[x] - Idxs[y]
                )  # m=dy/dx #if slope 0 then intercept does not exist constant y where y=b
                # intercept = h[Idxs[x]] - slope * Idxs[x] #y=mx+b, b=y-mx
                slopes[x].append((slope, y))
        for x in range(len(Idxs)):
            slopes[x].sort()  # key=lambda val: val[0])
            CurIdxs = [Idxs[x]]
            for y in range(0, len(slopes[x])):
                # distance = abs(slopes[x][y][2] * slopes[x][y+1][1] + slopes[x][y][3] - h[slopes[x][y+1][1]])
                CurIdxs.append(Idxs[slopes[x][y][1]])
                if len(CurIdxs) < 3:
                    continue
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
                    CurIdxs = [
                        CurIdxs[0],
                        CurIdxs[-1],
                    ]  # restart search from this point
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
        mtrend = [
            (
                pts,
                (
                    res[0],
                    res[1],
                    res[2],
                    res[3],
                    res[4],
                    measure_area((pts, res), isMin, h),
                ),
            )
            for pts, res in mtrend
        ]
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
        d_dx = FinDiff(
            0, dx, 1, acc=accuracy
        )  # acc=3 #for 5-point stencil, currenly uses +/-1 day only
        d2_dx2 = FinDiff(
            0, dx, 2, acc=accuracy
        )  # acc=3 #for 5-point stencil, currenly uses +/-1 day only

        def get_minmax(h):
            clarr = np.asarray(h, dtype=np.float64)
            mom, momacc = d_dx(clarr), d2_dx2(clarr)

            # print(mom[-10:], momacc[-10:])
            # numerical derivative will yield prominent extrema points only
            def numdiff_extrema(func):
                return [
                    x
                    for x in range(len(mom))
                    if func(x)
                    and (
                        mom[x] == 0
                        or (  # either slope is 0, or it crosses from positive to negative with the closer to 0 of the two chosen or prior if a tie
                            x != len(mom) - 1
                            and (
                                mom[x] > 0
                                and mom[x + 1] < 0
                                and h[x] >= h[x + 1]
                                or mom[x] < 0  # mom[x] >= -mom[x+1]
                                and mom[x + 1] > 0
                                and h[x] <= h[x + 1]
                            )
                            or x != 0  # -mom[x] >= mom[x+1]) or
                            and (
                                mom[x - 1] > 0
                                and mom[x] < 0
                                and h[x - 1] < h[x]
                                or mom[x - 1] < 0  # mom[x-1] < -mom[x] or
                                and mom[x] > 0
                                and h[x - 1] > h[x]
                            )
                        )
                    )
                ]  # -mom[x-1] < mom[x])))]

            return lambda x: momacc[x] > 0, lambda x: momacc[x] < 0, numdiff_extrema

        minFunc, maxFunc, numdiff_extrema = get_minmax(h)
        return numdiff_extrema(minFunc), numdiff_extrema(maxFunc)

    divide = list(reversed(range(len_h, -window, -window)))
    rem, divide[0] = window - len_h % window, 0
    if rem == window:
        rem = 0
    skey = 5  # if sortError else 5
    extremaIdxs = get_extrema(h, accuracy)
    mintrend, minwindows = calc_all(extremaIdxs[0], h, True)
    return mintrend, minwindows
