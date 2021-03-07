import threading

from broker.zerodha.zeroda_base import ZerodhaServiceBase


class QueueBasedServiceOnline(ZerodhaServiceBase):
    """
    Realtime tick provider data
    """

    def __init__(self, credential, configuration):
        super(QueueBasedServiceOnline, self).__init__(credential, configuration)
        self.intresting_stocks = self.configuration["stocks_to_subscribe"]
        self.intresting_stocks_full_mode = self.configuration["stocks_in_fullmode"]
        self.tickQueue = self.configuration["tickQueue"]
        self.q = self.tickQueue
        self.completion_event = self.configuration["completionEvent"]
        # Start warmup exercise in parallel
        self.warmup_tracker = {}
        self.warmup_thread = threading.Thread(
            target=self._preload_historical_data
        ).start()
        # self.warmup_thread.run()
        # initialize the thread to handle the tick data in a seperate
        self.queue_handler = threading.Thread(
            target=self.queue_based_tick_handler, args=()
        )
        self.queue_handler.start()

    def _check_shutdown_event(self):
        return self.completion_event.is_set()

    def init_listening(self):
        pass
