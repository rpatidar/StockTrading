import datetime


class NSETradingSystem:

    @staticmethod
    def isAfterMarketHours():
        now = datetime.datetime.today()
        return now < NINE_AM or now > FOUR_PM


# NINE_FIFTEEN_AM = today_date.replace(hour=9, minute=15, second=0, microsecond=0)
# NINE_THIRTY_AM = today_date.replace(hour=9, minute=30, second=0, microsecond=0)
# THREE_FORTY_PM = today_date.replace(hour=15, minute=40, second=0, microsecond=0)
# THREE_PM = today_date.replace(hour=15, minute=0, second=0, microsecond=0)
# THREE_FIFTEEN_PM = today_date.replace(hour=15, minute=15, second=0, microsecond=0)
# FOUR_PM = today_date.replace(hour=16, minute=0, second=0, microsecond=0)

# PRE_MARKET_TIME = (NINE_AM, NINE_THIRTY_AM)
# MARKET_TIME = (NINE_THIRTY_AM, THREE_FORTY_PM)
# POST_MARKET_TIME = (THREE_FORTY_PM, FOUR_PM)


def get_datetime(hour, minute):
    today_date = datetime.datetime.today()
    return today_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


HOLIDAYS = ["21-Feb-2020",
            "10-Mar-2020",
            "02-Apr-2020",
            "06-Apr-2020",
            "10-Apr-2020",
            "14-Apr-2020",
            "01-May-2020",
            "25-May-2020",
            "02-Oct-2020",
            "16-Nov-2020",
            "30-Nov-2020",
            "25-Dec-2020"]
HOLIDAYS = [datetime.datetime.strptime(d, '%d-%b-%Y').date() for d in HOLIDAYS]


def is_holiday(date):
    d = date
    if type(d) == datetime:
        d = date.date()
    return d.weekday() in [5, 6] or d in HOLIDAYS
