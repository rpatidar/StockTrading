import argparse
from strategy.trendlinestrategy import TrendlineStrategy
from broker.zerodha.zerodha_live_trading import ZerodhaServiceOnline
from broker.zerodha.zeroda_intraday_backtester import ZerodhaServiceIntraDay
from db import storage
from tradingsystem.tradingsystem import TradingSystem
from db.storage import StorageHandler
from db.tradebook import TradeBook
from trading_options import TradingOptions
import time
from broker.indan_stock import is_holiday, get_datetime
import datetime

"""
Trading System to Automate the Strategy execution in DB
1. It can listen to the tick data for a list of stock from the CSV File
2. It can insert the tick data into DB
3. It can execute the configured Strategy For specific stock
4. It can execute a default trading strategy

5. Risk management
6. Ordering Management - Can Resume the system from where it stopped.
7. Support the multiple trading platform

"""
import logging


def setup_logging():
    from logging.handlers import TimedRotatingFileHandler
    handler = TimedRotatingFileHandler('./logs/automatedtrader.log',
                                       when="h",
                                       interval=1,
                                       backupCount=5)
    logFormatter = logging.Formatter('%(asctime)s %(message)s')
    handler.suffix = "%Y-%m-%d"
    handler.setFormatter(logFormatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

def run():
    options = TradingOptions()
    sh = StorageHandler()
    tradeRunner = ZerodhaServiceOnline if options.args.mode == 'live' else ZerodhaServiceIntraDay
    credentials = {"api_key": "f6jdkd2t30tny1x8", "api_secret": "eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo"}
    configuration = None
    if options.args.mode == 'live':
        if is_holiday(datetime.datetime.now()):
            logging.info("Not Running the Live strategy today as date:{} is holiday".format(datetime.datetime.now()))
        configuration = {"stocks_to_subscribe": options.getStocks(), "stocks_in_fullmode": []}
    else:
        stock_input = dict((s, {"from": options.args.start, "to": options.args.end}) for s in options.getStocks())
        configuration = {"back_testing_config": {"stocks_config": stock_input}}
    # run trading system
    tradingSystem = TradingSystem(credentials, configuration, tradeRunner, [TrendlineStrategy()])
    tradingSystem.run()
    # Use tradebook and get summary
    tradeBook = TradeBook()
    if options.args.mode == 'live':
        # from db.shadow_trading_service import ShadowTradingService
        # tradeBook.register_trading_service(ShadowTradingService())
        from db.zeroda_live_trading_service import ZerodhaLiveTradingService
        tradeBook.register_trading_service(ZerodhaLiveTradingService(credentials))

    tradeBook.summary()
    if options.args.mode == 'live':
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
run()
