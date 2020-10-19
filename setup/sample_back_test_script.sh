#!/usr/bin/bash 
source ~/stock_trading_env/bin/activate
python3 ./bot_trading.py -f resource/stocks_100.txt -s "2020-10-01" -e "2020-10-15" audit

