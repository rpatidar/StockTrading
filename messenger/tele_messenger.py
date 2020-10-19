# Move this to a telegram bot class
import telegram

b = telegram.bot.Bot("1370331323:AAHe9lBTseBxn5KvA8v2SQbGp8RGbLToa30")
TELEGRAM_GROUP = -478351687


def send_message(msg):
    b.send_message(chat_id=TELEGRAM_GROUP, text=msg)
