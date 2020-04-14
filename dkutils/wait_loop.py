import time

from datetime import datetime


class WaitLoop:

    def __init__(self, sleep_secs, timeout_time):
        self.first_pass = True
        self.resume = True
        self._sleep_secs = sleep_secs
        self._timeout_time = timeout_time

    def __bool__(self):
        if self.first_pass:
            self.first_pass = False
        else:
            time.sleep(self._sleep_secs)
        self.resume = datetime.now() < self._timeout_time
        return self.resume
