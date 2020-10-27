import datetime
import threading
from collections import OrderedDict

from db.storage import StorageHandler


class Strategy:
    def __init__(self):

        self.stock_trading_days = {}
        pass

    def _get_create_or_get_day_history(
        self,
        script,
        timestamp,
        readonly=True,
        last_aggregate_date=None,
        aggregate=None,
        agg_type=1,
        last_aggregate_time=None,
    ):
        date = timestamp.date()

        if readonly:
            script_history = self.market_history.get(script)
            return script_history[date] if script_history != None else None

        script_history = self.market_history.setdefault(
            script, {"1minute": OrderedDict, "5minute": OrderedDict()}
        )[str(agg_type) + "minute"]

        # script_history = self.market_history.setdefault(script, OrderedDict())

        if aggregate != None:
            trading_data = script_history.setdefault(
                date, {"date": date, "trading_data": []}
            )
            if (
                len(trading_data["trading_data"]) > 0
                and trading_data["trading_data"][-1]["date"] == last_aggregate_time
            ):
                trading_data["trading_data"][-1] = aggregate
            else:
                trading_data["trading_data"].append(aggregate)
            return trading_data

        else:
            print(
                "Ignoring the script update="
                + str(script)
                + " on date="
                + str(timestamp)
                + " because of null data"
            )
            return None

    def _update_local_cache(self, tick_data, timestamp, agg_type=1):
        """
        I personally don't like the way this method is written, just thought to build some aggregate by date for easy processing.
        The task of this function is to update the aggregate of previous timestamp in the local cache if not already done.

        Working logic of this method:
        1. We only update the aggregated data which is completed, partial completed data is not updated
        2. Data is pulled from the central Stored cache and current tick data does not impact anything.
        3. If current tick is for 9:26:00 , this will be updating the aggregated for 9:20 to 9:25.
        """

        (
            current_minute,
            current_date,
            last_aggregate_time,
        ) = self.get_previous_aggregate_timestamp(timestamp, agg_type)
        instrument_token = tick_data["instrument_token"]
        last_aggregate_date = last_aggregate_time.date()
        # Only get the data for the last datapoint
        last_stock_trading_data = self.get_simple_day_history(
            last_aggregate_date,
            instrument_token,
            last_aggregate_time=last_aggregate_time,
            agg_type=agg_type,
        )
        if last_stock_trading_data != None:
            self._get_create_or_get_day_history(
                instrument_token,
                timestamp,
                readonly=False,
                last_aggregate_date=last_aggregate_date,
                aggregate=last_stock_trading_data[0],
                agg_type=agg_type,
                last_aggregate_time=last_aggregate_time,
            )
        pass

    def get_previous_aggregate_timestamp(self, timestamp, agg_type=1):
        current_minute = timestamp.replace(
            minute=int(timestamp.minute / agg_type) * agg_type, second=0, microsecond=0
        )
        minute_delta = datetime.timedelta(minutes=agg_type)
        current_date = timestamp.date()
        last_aggregate_time = current_minute - minute_delta
        return current_minute, current_date, last_aggregate_time

        pass

    def get_trading_history_for_day(self, script, date, previous_day, agg_type=1):
        script_all_aggregate = self.market_history.get(script)
        if script_all_aggregate == None:
            return None

        script_history = script_all_aggregate.get(str(agg_type) + "minute")
        date_to_fetch = date
        if previous_day:
            time_delta = datetime.timedelta(
                max(1, (date_to_fetch.weekday() + 6) % 7 - 3)
            )
            date_to_fetch = date_to_fetch - time_delta

        if script_history != None and date_to_fetch in script_history:
            return script_history[date_to_fetch]
        else:
            return None

    def to_date(self, trading_data_day):
        data = []
        if trading_data_day == None:
            return data
        for ohlc in trading_data_day["trading_data"]:
            data.append(ohlc["date"])
        return data

    def holc_to(self, trading_data_day, type):
        data = []
        if trading_data_day == None:
            return data
        for ohlc in trading_data_day["trading_data"]:
            data.append(ohlc["low"])
        return data

    def get_simple_day_history(
        self, date, instrument_token, last_aggregate_time=None, agg_type=1
    ):
        sh = StorageHandler()
        full_stock_history = sh.get_db().get(instrument_token, None)
        required_data = []

        if full_stock_history == None:
            return None

        if last_aggregate_time != None:
            res = full_stock_history.get(str(agg_type) + "minute").get(
                last_aggregate_time
            )
            if res == None:

                return None
            else:
                return [res]
        return None

    def run(self, tick_data, timestamp):
        pass
