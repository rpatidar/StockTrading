curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
python3 -m pip install virtualenv
python3 -m virtualenv -ppython3 stock_trading_env
sudo apt-get install build-essential libffi-dev python-dev-is-python3 python3-dev
source stock_trading_env/bin/activate
pip3 install matplotlib kiteconnect findiff numpy python-telegram-bot pandas

