import sys
import datetime
import logging
import time
import os
from broker.indan_stock import is_holiday, get_datetime
from broker.zerodha.zeroda_intraday_backtester import ZerodhaServiceIntraDay
from broker.zerodha.zerodha_live_trading import ZerodhaServiceOnline
from db.storage import StorageHandler
from db.tradebook import TradeBook
from strategy.trendlinestrategy import TrendlineStrategy
from trading_options import TradingOptions
from tradingsystem.tradingsystem import TradingSystem


def setup_logging():
    from logging.handlers import TimedRotatingFileHandler

    handler = TimedRotatingFileHandler(
        "./logs/automatedtrader.log", when="h", interval=1, backupCount=5
    )
    logFormatter = logging.Formatter("%(asctime)s %(message)s")
    handler.setFormatter(logFormatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def run():
    options = TradingOptions()
    sh = StorageHandler()
    tradeRunner = (
        ZerodhaServiceOnline if options.args.mode == "live" else ZerodhaServiceIntraDay
    )
    credentials = {
        "api_key": "f6jdkd2t30tny1x8",
        "api_secret": "eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo",
    }
    configuration = None
    if options.args.mode == "live":
        if os.path.exists("tmp/session_file"):
            os.remove("./tmp/session_file")

        if is_holiday(datetime.datetime.now()):
            logging.info(
                "Not Running the Live strategy today as date:{} is holiday".format(
                    datetime.datetime.now()
                )
            )
        configuration = {
            "stocks_to_subscribe": options.getStocks(),
            "stocks_in_fullmode": [],
        }
    else:
        stock_input = dict(
            (s, {"from": options.args.start, "to": options.args.end})
            for s in options.getStocks()
        )
        configuration = {"back_testing_config": {"stocks_config": stock_input}}
    # run trading system
    tradingSystem = TradingSystem(
        credentials, configuration, tradeRunner, [TrendlineStrategy()]
    )
    tradingSystem.run()
    # Use tradebook and get summary
    tradeBook = TradeBook()
    if options.args.mode == "live":
        # from db.shadow_trading_service import ShadowTradingService
        # tradeBook.register_trading_service(ShadowTradingService())
        from db.zeroda_live_trading_service import ZerodhaLiveTradingService

        tradeBook.register_trading_service(ZerodhaLiveTradingService(credentials))

    tradeBook.summary()
    if options.args.mode == "live":
        print("Waiting till ", str(get_datetime(16, 00)))
        time.sleep((get_datetime(16, 00) - datetime.datetime.now()).total_seconds())
        tradingSystem.shutdown()


# logging.basicConfig(filename='./automatedtrader.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Uncomment to profile the code
# import yappi
# yappi.set_clock_type("cpu") # Use set_clock_type("wall") for wall time
# yappi.start()
# play_casino()
# play_casino()
# yappi.get_func_stats().print_all()
# yappi.get_thread_stats().print_all()

# Command line Running argument
# -l "RELIANCE" -s "2020-09-01" -e "2020-09-30"  live/audit


# Execute the command
setup_logging()

try:
    run()
except:
    e = sys.exc_info()
    logging.error("Error while executing the bot trading", exc_info=e)
    print("Error while executing the Bot trading:\n {0}".format((str(e))))
