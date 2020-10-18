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

from utils.objecthelpers import Singleton


class StorageHandler(metaclass=Singleton):
    def __init__(self):
        self.storage = {}
        self.strategy_context = {}

    def get_db(self):
        return self.storage

    def get_st_context(self):
        return self.strategy_context
