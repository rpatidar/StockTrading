import sys
import datetime
import logging
import time

from strategy.range_breakout import RangeBreakout
from strategy.supertrendstrategy import SuperTrendStrategy
from strategy.sma_crossover import SMACrossOver
from strategy.mean_reversion_rsi import RSIMeanReversion
from utility_programs.analyze_summery import generate_summery
from api.bot_api import api_controller
from broker.indan_stock import get_datetime
from broker.zerodha.zeroda_intraday_backtester import ZerodhaServiceIntraDay
from broker.zerodha.zerodha_live_trading import ZerodhaServiceOnline
from db.tradebook import TradeBook
from bot_logging.setup_logger import setup_logging
from strategy.trendlinestrategy import TrendlineStrategy
from trading_options import TradingOptions
from tradingsystem.tradingsystem import TradingSystem
import traceback
from messenger.tele_messenger import Messenger
from db.zeroda_live_trading_service import ZerodhaLiveTradingService
from broker.zerodha.queue_live_trading import QueueBasedServiceOnline
import multiprocessing as mp
from broker.zerodha.login_helper import prerequisite_multiprocess
import multiprocessing
from utils.credential_helper import get_zerodha_credentails
import threading
credentials = get_zerodha_credentails()
PROXY = "http://127.0.0.1:6060"


def run(options, start_index, end_index, psnumber, tickQueue, completion_event):
    setup_logging("strategyrunner_" + str(psnumber))
    trade_runner = (
        QueueBasedServiceOnline
        if options.args.mode == "live" or options.args.mode == "audit"
        else ZerodhaServiceIntraDay
    )

    configuration = None
    if options.args.mode == "live" or options.args.mode == "audit":
        # if is_holiday(datetime.datetime.now()):
        #     logging.info(
        #         "Not Running the Live strategy today as date:{} is holiday".format(
        #             datetime.datetime.now()
        #         )
        #     )
        configuration = {
            "stocks_to_subscribe": options.getStocks()[start_index:end_index],
            "stocks_in_fullmode": [],
            "tickQueue": tickQueue,
            "completionEvent": completion_event,
            "proxy": PROXY,
            "mode": options.args.mode,
        }
    else:
        stock_input = dict(
            (
                s,
                {
                    "from": datetime.datetime.strptime(options.args.start, "%Y-%m-%d"),
                    "to": datetime.datetime.strptime(options.args.end, "%Y-%m-%d"),
                },
            )
            for s in options.getStocks()[start_index:end_index]
        )
        #Hard coding to run on NIFTY BANK as space are not supported
        # stock_input = {
        #         "NIFTY BANK": {
        #             "from": datetime.datetime.strptime(options.args.start, "%Y-%m-%d"),
        #             "to": datetime.datetime.strptime(options.args.end, "%Y-%m-%d"),
        #     }
        # }

        configuration = {
            "back_testing_config": {"stocks_config": stock_input},
            "proxy": PROXY,
            "mode": options.args.mode,
        }

    # Use tradebook and get summary
    tradeBook = TradeBook()
    if options.args.mode == "live" or options.args.mode == "audit":
        tradeBook.register_trading_service(
            ZerodhaLiveTradingService(
                credentials, {"proxy": PROXY, "mode": options.args.mode}
            )
        )
    else:
        # TODO: This will need some modification
        tradeBook.register_trading_service(
            ZerodhaLiveTradingService(
                credentials, {"proxy": PROXY, "mode": options.args.mode}
            )
        )

    stry = {"meanreversion": RSIMeanReversion,
            "supertrend": SuperTrendStrategy,
            "openingrangebreakout": RangeBreakout,
            "smacrossover": SMACrossOver}[options.args.tradingstrategy]

    # run trading system
    tradingSystem = TradingSystem(
        credentials, configuration, trade_runner, [stry()]
    )

    tradingSystem.run()

    if options.args.mode == "live" or options.args.mode == "audit":
        completion_event.wait()
        time.sleep(5)


def main():
    setup_logging("main")
    options = TradingOptions()
    messenger = Messenger(options.args.mode)
    clean_credentials = False  # options.args.mode == "live"
    prerequisite_multiprocess(
        credentials["api_key"], credentials["api_secret"], clean_credentials
    )

    process_controller = mp.Process if options.args.multiprocess else threading.Thread

    completion_event = mp.Event()

    # Server Process to listen to the api calls and server the get put events.
    server = process_controller(
        target=api_controller, args=(completion_event, credentials, options.args.mode)
    )
    server.start()
    time.sleep(2)
    try:
        print("S :" + str(datetime.datetime.now()))
        ps, broadcastQ = trigger_childprocess(completion_event, options, process_controller)
        if options.args.mode == "live" or options.args.mode == "audit":
            handle_realtime_trades(broadcastQ, completion_event, options, server)
        else:
            handle_backtest_trades(completion_event, ps, server)
    except:
        traceback.print_exc()
        e = sys.exc_info()
        logging.error("Error while executing the bot trading", exc_info=e)
        print("Error while executing the Bot trading:\n {0}".format((str(e))))

        if options.args.mode == "live" or options.args.mode == "audit":
            messenger.send_message(
                "Live trading program crashed because of some issue, please check\n"
                + str(e)
            )
    print("E :" + str(datetime.datetime.now()))
    generate_summery(summery_file="./tmp/summery/history.json")


def trigger_childprocess(completion_event, options, process_controller):
    broadcastQ = []
    ps = []
    nstocks = len(options.getStocks())
    ncpu = 1 #multiprocessing.cpu_count()
    if ncpu > 1:
        ncpu = ncpu - 1
    steps = int(nstocks / ncpu)
    if steps == 0:
        steps = nstocks
    for i in range(0, nstocks, steps):
        q = mp.Queue()
        broadcastQ.append(q)
        start_index = i
        end_index = i + steps
        process_number = str(i / steps)
        # Smaller process to server the specific type of trend detection on some CPU

        p = process_controller(
            target=run,
            args=(
                options,
                start_index,
                end_index,
                process_number,
                q,
                completion_event,
            ),
        )
        p.start()
        ps.append(p)
    return ps, broadcastQ


def handle_backtest_trades(completion_event, ps, server):
    for p in ps:
        p.join()
    completion_event.set()
    time.sleep(5)
    server.terminate()
    server.join()


def handle_realtime_trades(broadcastQ, completion_event, options, server):
    def publish_to_threads(ticks, timestamp, backfill):
        if completion_event.is_set():
            return
        for q in broadcastQ:
            q.put((ticks, timestamp))

    tick_data_updater = ZerodhaServiceOnline(
        credentials,
        {
            "stocks_to_subscribe": options.getStocks(),
            "stocks_in_fullmode": [],
            "completionEvent": completion_event,
            "warmupDisabled": True,
            "mode": options.args.mode,
        },
    )
    tick_data_updater.on_tick_update(publish_to_threads)
    tick_data_updater.init_listening()
    four_pm = get_datetime(16, 00)
    while datetime.datetime.now() < four_pm and not completion_event.is_set():
        time.sleep(2)
    if completion_event.is_set():
        logging.info("Shutting down because of external event to close the process")
        time.sleep(2)
        server.terminate()
    elif datetime.datetime.now() > four_pm:
        logging.info("Shutting down as non trading time")
        completion_event.set()
        time.sleep(2)
        server.terminate()
    else:
        raise Exception("Not possible")


# Everything begins here
if __name__ == "__main__":
    main()
