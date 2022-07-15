import logging
import time

from functools import wraps
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)


def retry_50X_httperror(tries=3, delay=2, backoff=2):
    """
    Retry calling the decorated function using an exponential backoff.

    Based on:
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    Parameters
    ----------
    tries: int
        Number of times to try (not retry) before giving up
    delay: int
        Initial delay between retries in seconds
    backoff: int
        Backoff multiplier e.g. value of 2 will double the delay each retry
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except HTTPError as e:
                    status_code = e.response.status_code
                    if 500 <= status_code < 600:
                        logger.warning(f'{str(e)}, Retrying in {mdelay} seconds...')
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                    else:
                        raise

            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
