from datetime import datetime


def get_utc_timestamp():
    """
    Order run timings (i.e. start-time, end-time, and duration) are in milliseconds since the epoch
    date (i.e. 1/1/1970) in UTC. This function returns the current time in this format so it
    can be compared with order run timings. This was derived from DKModules DKDateUtils.py
    get_utc_timestamp() function.

    Returns
    -------
    int
        Current UTC time in milliseconds since the epoch date (i.e. 1/1/1970).
    """
    return int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000)
