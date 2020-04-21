import time

from unittest import TestCase

from dkutils.wait_loop import WaitLoop


class TestWaitLoop(TestCase):

    def test_wait_loop(self):
        sleep_secs = 1
        duration_secs = 5
        wait_loop = WaitLoop(sleep_secs, duration_secs)

        iterations = 0
        start_time = time.time()
        while wait_loop:
            iterations += 1

        elapsed_time = time.time() - start_time
        msg = f'Elapsed time ({elapsed_time}) should be > wait loop timeout ({duration_secs})'
        self.assertGreaterEqual(elapsed_time, duration_secs, msg)
