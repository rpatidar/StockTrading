
# Installation
1. Anaconda : https://docs.anaconda.com/anaconda/install/mac-os/
1. Create new conda environment : 'conda create -n stocktrading python=3.6'
1. Activate conda environment : 'conda activate stocktrading'
1. Install numpy in environment : 'conda install numpy'
1. Install matplotlib : 'conda install matplotlib'
1. Install kiteconnect : 'pip install kiteconnect'
1. Install findiff : 'pip install findiff'

# Execution
> python3.6 AutomatedTradingSystem.py audit --start 2020-09-01 --end 2020-09-30 -l ENDURANCE
> python3.6 AutomatedTradingSystem.py live --start 2020-09-01 --end 2020-09-30 -l ENDURANCE
> python3.6 AutomatedTradingSystem.py audit --start 2020-09-01 --end 2020-09-30 -f '../stock.txt'
> python AutomatedTradingSystem.py live -f D:\workspace\stocks_100.txt

# Debug
## If getting error "ModuleNotFoundError: No module named 'zerodha'"
Chage import line in top of file in AutomatedTradingSystem.py and broker/zerodha/zeroda_intraday_backtester.py.
Instead of having 'from zerodha.zeroda_intraday_backtester import ZerodhaServiceIntraDay' change it to 'from broker.zerodha.zeroda_intraday_backtester import ZerodhaServiceIntraDay'

# Issues
1. Start time and end time conditon updated in /broker/zerodha/zerodha_live_trading.py
2. /broker/zerodha/zeroda_base.py : filehandler failing due to file path in Windows.
3. Main thread getting blocked. Need debug.