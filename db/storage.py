
"""
Strcuture of the data stored in the storage is
{
    "instrument_token_id_XXXX": {
        "1minute": {
            "datetime(x,y,z, m,n)"  : {'high' : "A", "low": "B", "open": "X", "close": "Z"}
        }
    }
}
"""
global storage
global strategy_context

def init():
    global storage, strategy_context
    storage = {}
    strategy_context = {}

def get_db():
    global storage, strategy_context
    return storage

def get_st_context():
    global strategy_context
    return strategy_context