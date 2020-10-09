import os
import json

pl_summery = json.load(open("./tmp/summery/trendline1.json", "r"))
total_pl = 0
max_loss = 0
for e in pl_summery:
    total_pl = total_pl + e['pl-percentage']
    max_loss = min(e['pl-percentage'], max_loss)
print("Total PL: = {}", (str(total_pl)))
print("Total trades done=" + str(len(pl_summery)))

print("Max Loss:" + str(max_loss))  