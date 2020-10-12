import datetime


class NSETradingSystem:

    @staticmethod
    def isAfterMarketHours():
        now = datetime.datetime.today()
        return now < NINE_AM or now > FOUR_PM


today_date = datetime.datetime.today()
NINE_AM = today_date.replace(hour=9, minute=0, second=0, microsecond=0)
NINE_FIFTEEN_AM = today_date.replace(hour=9, minute=15, second=0, microsecond=0)
NINE_THIRTY_AM = today_date.replace(hour=9, minute=30, second=0, microsecond=0)
THREE_FORTY_PM = today_date.replace(hour=15, minute=40, second=0, microsecond=0)
THREE_PM = today_date.replace(hour=15, minute=0, second=0, microsecond=0)
THREE_FIFTEEN_PM = today_date.replace(hour=15, minute=15, second=0, microsecond=0)
FOUR_PM = today_date.replace(hour=16, minute=0, second=0, microsecond=0)
PRE_MARKET_TIME = (NINE_AM, NINE_THIRTY_AM)
MARKET_TIME = (NINE_THIRTY_AM, THREE_FORTY_PM)
POST_MARKET_TIME = (THREE_FORTY_PM, FOUR_PM)
