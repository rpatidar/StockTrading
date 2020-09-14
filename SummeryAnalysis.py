import os
import json
pl_summery = json.load(open("./tmp/summery/trnedline1.json","r"))
total_pl = 0
for e in pl_summery:
    total_pl = total_pl + e['pl-percentage']
print("Total PL: = {}", (str(total_pl)))
print("Total trades done=" + str(len(pl_summery)))

