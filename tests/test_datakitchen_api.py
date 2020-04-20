from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError

from dkutils.datakitchen_api import get_headers, create_order

DUMMY_AUTH_TOKEN = 'DATAKITCHEN_TOKEN'
DUMMY_HEADERS = {'Authorization': f'Bearer {DUMMY_AUTH_TOKEN}'}


class TestDatakitchenAPI(TestCase):

    @patch('dkutils.datakitchen_api.requests.post')
    def test_get_headers(self, mock_post):
        mock_post.return_value.text = DUMMY_AUTH_TOKEN
        headers = get_headers('Foo', 'Bar')
        self.assertEqual(headers, DUMMY_HEADERS)

    def test_get_headers_exception(self):
        with self.assertRaises(HTTPError):
            get_headers('Foo', 'Bar')

    @patch('dkutils.datakitchen_api.requests.put')
    def test_create_order(self, mock_put):
        response_json = {
            "order_id": "abd8c538-705d-11ea-99d3-2699c9f5d2a0",
            "variable_overrides": {},
            "status": "success"
        }
        mock_put.return_value.json = lambda: response_json
        response = create_order(DUMMY_HEADERS, 'kitchen', 'recipe', 'variation')
        self.assertEqual(response.json(), response_json)

    def test_create_order_exception(self):
        with self.assertRaises(HTTPError):
            create_order(DUMMY_HEADERS, 'kitchen', 'recipe', 'variation')
