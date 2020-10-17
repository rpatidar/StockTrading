import pickle

file = "./tmp/HINDZINC_364545_2020-08-01---2020-08-31"
data = pickle.load(open(file, "rb"))
day_data = []
for d in data:
    if data[0]['date'].replace(hour=0, minute=0, second=0, microsecond=0) == data[0]['date'].replace(hour=0, minute=0,
                                                                                                     second=0,
                                                                                                     microsecond=0):
        day_data.append(d)

d = "low,high,open,close" + '\n'.join(
    [str(dd['low']) + "," + str(dd['high']) + "," + str(dd['open']) + "," + str(dd['close']) for dd in day_data])
# print(d)

import datetime

print("StartTime" + str(datetime.datetime.now()))
for x in range(5000):
    with open("./tmp/test", "w") as test:
        test.write(d[:x])
print("EndTime" + str(datetime.datetime.now()))

# print("StartTime"+ str(datetime.datetime.now()))
# for x in range(7872*300*2):
#     with open("./tmp/test", "r") as test:
#         test.readlines()
# print("EndTime"+  str(datetime.datetime.now()))
