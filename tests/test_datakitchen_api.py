from unittest import TestCase

from requests.exceptions import HTTPError

from dkutils.datakitchen_api import get_headers


class TestDatakitchenAPI(TestCase):

    def test_get_headers(self):
        with self.assertRaises(HTTPError):
            get_headers('Foo', 'Bar')
