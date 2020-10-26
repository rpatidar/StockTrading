import argparse


class TradingOptions:
    def __init__(self):
        # Create the parser
        self.parser = argparse.ArgumentParser(
            description="Automatically trade the equities"
        )
        # Add the arguments
        # Addng positional arguments
        self.parser.add_argument(
            "mode",
            type=str,
            choices=["backtest", "audit", "live"],
            help="comma separated list of stock codes",
        )
        # Adding optional arguments
        self.parser.add_argument(
            "-l", "--list", type=str, nargs="+", help="list of stock codes"
        )
        self.parser.add_argument(
            "-f", "--file", type=str, help="file with list of stock codes"
        )
        self.parser.add_argument(
            "-s", "--start", type=str, help="start date", default="2019-12-01"
        )
        self.parser.add_argument(
            "-e", "--end", type=str, help="end date", default="2019-12-31"
        )
        # Execute the parse_args() method
        self.args = self.parser.parse_args()

    def getStocks(self):
        if self.args.list is not None:
            return self.args.list
        stocks = []
        with open(self.args.file) as f:
            for content in f:
                stocks.extend([x.strip() for x in content.split(" ")])
        return stocks
