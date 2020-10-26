# Move this to a telegram bot class
import telegram

from utils.objecthelpers import Singleton

TELEGRAM_GROUP = -478351687

class Messenger(metaclass=Singleton):
    def __init__(self, mode):
        self.bot = telegram.bot.Bot("1370331323:AAHe9lBTseBxn5KvA8v2SQbGp8RGbLToa30")
        self.mode = mode
    
    def send_message(self, msg):
        print(msg)
        if self.mode == "live":
            self.bot.send_message(chat_id=TELEGRAM_GROUP, text=msg)
        pass
