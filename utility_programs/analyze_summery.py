import json

history = json.load(open("../tmp/summery/history.json", "r"))
print(history)
# total_pl = 0
# max_loss = 0
# for e in pl_summery:
#     total_pl = total_pl + e["pl-percentage"]
#     max_loss = min(e["pl-percentage"], max_loss)
# print("Total PL: = {}", (str(total_pl)))
# print("Total trades done=" + str(len(pl_summery)))
#
# print("Max Loss:" + str(max_loss))
trades = []
import datetime

total_pl = 0
for stock, stock_history in history.items():
    for t in stock_history:
        pl = ((t["exit_price"] - t["entry_price"]) / t["exit_price"]) * 100
        total_pl = pl + total_pl
        trades.append(
            {
                "stock": stock,
                "enter_date": datetime.datetime.fromtimestamp(t["entry_time"]),
                "exit_date": datetime.datetime.fromtimestamp(t["exit_time"]),
                "entry_price": t["entry_price"],
                "exit_time": t["exit_price"],
                "type": t["type"],
                "profit_loss": pl,
            }
        )

import pandas as pd

df = pd.DataFrame(trades)
print(df.to_string())

print("=========================================\n")
print("Total Profit/Loss = {}".format(total_pl))
