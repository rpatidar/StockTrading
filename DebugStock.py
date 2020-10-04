import os
import json
history = json.load(open("./tmp/summery/history.json","r"))
import plotly.graph_objects as go
import plotly as py
import pandas as pd
from datetime import datetime
from datetime import datetime
import dateutil.parser

import pandas as pd
import pickle
def get_instrument():
    filehandler = open("./tmp/instruments", 'rb')
    instrument = pickle.load(filehandler)
    filehandler.close()
    return instrument


def get_instrument_id(stockid, exchange):
    instruments = get_instrument()
    for instrument in instruments:
        if instrument['tradingsymbol'] == stockid and instrument['exchange'] == exchange:
            return instrument['instrument_token']
    return None


def get_historical(stock_name, instrument_token, from_date, to_date):
    chart_cache_name = stock_name + "_" + str(instrument_token) + "_" + str(from_date) + "---" + str(
        to_date)
    filehandler = open("./tmp/" + chart_cache_name, 'rb')
    stock_data = pickle.load(filehandler)
    filehandler.close()
    return stock_data


instrument_id = get_instrument_id('JINDALSTEL', 'NSE')

stock_trading_history = history.get(str(instrument_id))
historical = get_historical('JINDALSTEL', instrument_id, "2019-12-01", "2019-12-31")

df = pd.DataFrame(historical)
df.set_index('date')


layout = go.Layout(
    xaxis=dict(rangebreaks=[
        dict(bounds=["sat", "mon"]), # hide weekends
        dict(values=["2019-12-25", "2020-01-01"]), # hide Christmas and New Year's,
        { 'pattern': 'hour', 'bounds': [16, 9] }
        ],
    )
)

points = []
for x in stock_trading_history :
    points.append([{'price' : z['price'], 'date': dateutil.parser.parse(z['date']) } for z in x['execution_info']['trend_info']['trendpoints']])


#"%Y-%m-%d %H:%M:%S%z"
# points = [{'price' : x['price'], 'date': dateutil.parser.parse(x['date']) } for x in points]
#ppd = pd.DataFrame(points)

# ppd.set_index('date')
# price_points = ppd['price']
# x_points = ppd['date']
data=[go.Candlestick(x=df['date'],
                                     open=df['open'],
                                     high=df['high'],
                                     low=df['low'],
                                     close=df['close'])]
for p in points:
    ppd = pd.DataFrame(p)
    print(ppd)
    price_points = ppd['price']
    x_points = ppd['date']
    data.append(dict( x=x_points, y=price_points, type='scatter',
                         marker = dict( color = 'blue' ),
                          name='Trendline', mode='lines'))

fig = go.Figure(data=data,layout=layout)


py.offline.plot(fig)

