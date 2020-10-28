import logging


def setup_logging(pnumber):
    from logging.handlers import TimedRotatingFileHandler

    handler = TimedRotatingFileHandler(
        "./logs/automatedtraderlog." + str(pnumber),
        when="h",
        interval=1,
        backupCount=5,
    )
    logFormatter = logging.Formatter("%(asctime)s %(message)s")
    handler.setFormatter(logFormatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
