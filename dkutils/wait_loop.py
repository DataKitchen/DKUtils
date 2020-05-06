import time

from datetime import datetime, timedelta


class WaitLoop:

    def __init__(self, sleep_secs, duration_secs):
        """
        WaitLoop is for use in a while loop. Create an instance of this class and add
        it as the condition/expression to the while loop.

        Parameters
        ----------
        sleep_secs : int
            Number of seconds to sleep in between loop executions.
        duration_secs : int
            Max duration in seconds after which the loop will exit.
        """
        self.first_pass = True
        self.resume = True
        self._sleep_secs = sleep_secs
        self._timeout_time = datetime.now() + timedelta(seconds=duration_secs)

    def __bool__(self):
        """
        Determines if the loop should exit.

        Returns
        -------
        bool
            True if loop should exit, False otherwise.
        """
        if self.first_pass:
            self.first_pass = False
        else:
            time.sleep(self._sleep_secs)
        self.resume = datetime.now() < self._timeout_time
        return self.resume
