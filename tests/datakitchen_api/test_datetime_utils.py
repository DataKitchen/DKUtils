from unittest import TestCase

from datetime import datetime

from dkutils.datakitchen_api.datetime_utils import get_utc_timestamp


class TestDatetimeUtils(TestCase):

    def test_get_utc_timestamp(self):
        utc_timestamp = get_utc_timestamp()
        derived_utc_time = datetime.fromtimestamp(utc_timestamp / 1000)
        cur_utc_time = datetime.utcnow()
        self.assertGreater(cur_utc_time, derived_utc_time)
