import datetime
import logging
import threading

from flask import request, render_template

from bot_logging.setup_logger import setup_logging
from db.zeroda_live_trading_service import ZerodhaLiveTradingService


def api_controller(completion_event, credentials, mode):
    setup_logging("apihandler")
    from flask import Flask
    from waitress import serve
    from flask_cors import CORS

    app = Flask(__name__, template_folder="../templates")
    CORS(app, resources={r"/*": {"origins": "*"}})
    from broker.zerodha.zeroda_base import ZerodhaServiceBase
    import json

    base = ZerodhaServiceBase(credentials, None)
    live_trading = ZerodhaLiveTradingService(credentials, {"mode": mode})

    def summery_dump():
        completion_event.wait()
        live_trading.summery()
        logging.info("Completed the summery generation")

    threading.Thread(target=summery_dump).start()

    @app.route("/", methods=["GET"])
    def home():
        test = "I am a sample Input on html page"
        return render_template("index.html", test=test)

    @app.route("/instruments", methods=["GET"])
    def get_instruments():
        inst = []
        for i in base.get_instruments():
            inst.append(
                {
                    "instrument_token": i["instrument_token"],
                    "exchange": i["exchange"],
                    "tradingsymbol": i["tradingsymbol"],
                }
            )
        return json.dumps(inst)

    @app.route("/enter", methods=["POST"])
    def enter_trade():
        args = request.json
        trade_type, instrument_token, date, price, strategy, strategycontext = (
            args.get("trade_type"),
            args.get("instrument_token"),
            args.get("date"),
            args.get("price"),
            args.get("strategy"),
            args.get("strategycontext"),
        )
        live_trading.enter(
            trade_type, instrument_token, date, price, strategy, strategycontext
        )
        return "{}"

    pass

    @app.route("/exit", methods=["POST"])
    def exit_trade():
        args = request.json
        trade_type, instrument_token, date, price, strategy, strategycontext = (
            args.get("trade_type"),
            args.get("instrument_token"),
            args.get("date"),
            args.get("price"),
            args.get("strategy"),
            args.get("strategycontext"),
        )
        live_trading.exit(
            trade_type, instrument_token, date, price, strategy, strategycontext
        )
        return "{}"

    pass

    @app.route("/historical_data", methods=["POST", "GET"])
    def historical_data():
        args = request.json
        instrument_token, from_date, to_date, aggregate_type, continuous, oi = (
            args.get("instrument_token"),
            args.get("from_date"),
            args.get("to_date"),
            args.get("aggregate_type"),
            args.get("continuous"),
            args.get("oi"),
        )

        stock_name, exchange = base.get_symbol_and_exchange(instrument_token)
        hist_data = base.get_trading_data(
            stock_name,
            instrument_token,
            datetime.datetime.fromtimestamp(from_date),
            datetime.datetime.fromtimestamp(to_date),
        )
        for d in hist_data:
            d["date"] = d["date"].timestamp()
        return json.dumps(hist_data)

    @app.route("/shutdown", methods=["POST", "GET"])
    def shutdown():
        completion_event.set()
        return """{'message': 'Shutdown flag is set' }"""

    serve(app, port=6060)
