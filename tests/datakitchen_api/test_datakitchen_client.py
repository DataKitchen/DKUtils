from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError

from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient

DUMMY_URL = 'https://dummy/url'
DUMMY_AUTH_TOKEN = 'DATAKITCHEN_TOKEN'
DUMMY_HEADERS = {'Authorization': f'Bearer {DUMMY_AUTH_TOKEN}'}
NONE_TOKEN_HEADERS = {'Authorization': 'Bearer None'}
DUMMY_USERNAME = 'dummy_username'
DUMMY_PASSWORD = 'dummy_password'
DUMMY_CREDENTIALS = {'username': DUMMY_USERNAME, 'password': DUMMY_PASSWORD}
DUMMY_KITCHEN = 'dummy_kitchen'
DUMMY_RECIPE = 'dummy_recipe'
DUMMY_VARIATION = 'dummy_variation'
DUMMY_PARAMETERS = {}
DUMMY_ORDER_ID = 'dummy_order_id'


class TestDataKitchenClient(TestCase):

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_without_token(self, mock_post, mock_get):
        mock_get.return_value.raise_for_status.side_effect = HTTPError('Failed API Call')
        mock_post.return_value.text = DUMMY_AUTH_TOKEN
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        mock_get.assert_called_with(f'{DUMMY_URL}/v2/validatetoken', headers=NONE_TOKEN_HEADERS)
        mock_post.assert_called_with(f'{DUMMY_URL}/v2/login', data=DUMMY_CREDENTIALS)
        self.assertEqual(dk_client._headers, DUMMY_HEADERS)
        self.assertEqual(dk_client._token, DUMMY_AUTH_TOKEN)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_with_token(self, mock_post, mock_get):
        dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, token=DUMMY_AUTH_TOKEN, base_url=DUMMY_URL
        )
        mock_get.assert_called_with(f'{DUMMY_URL}/v2/validatetoken', headers=DUMMY_HEADERS)
        mock_post.assert_not_called()
        self.assertEqual(dk_client._headers, DUMMY_HEADERS)
        self.assertEqual(dk_client._token, DUMMY_AUTH_TOKEN)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_with_kitchen(self, *args):
        dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL, kitchen=DUMMY_KITCHEN
        )
        self.assertEqual(dk_client._kitchen, DUMMY_KITCHEN)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_with_recipe(self, *args):
        dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL, recipe=DUMMY_RECIPE
        )
        self.assertEqual(dk_client._recipe, DUMMY_RECIPE)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_with_variation(self, *args):
        dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL, variation=DUMMY_VARIATION
        )
        self.assertEqual(dk_client._variation, DUMMY_VARIATION)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_missing_attributes(self, mock_post, mock_get):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError):
            dk_client.create_order()

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.create_order')
    def test_create_order(self, mock_create_order, mock_post, mock_get):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        dk_client.create_order()
        mock_create_order.assert_called_with(
            NONE_TOKEN_HEADERS,
            DUMMY_KITCHEN,
            DUMMY_RECIPE,
            DUMMY_VARIATION,
            datakitchen_url=DUMMY_URL,
            parameters=DUMMY_PARAMETERS
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.get_order_runs')
    def test_get_order_runs(self, mock_get_order_runs, mock_post, mock_get):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        dk_client.get_order_runs(DUMMY_ORDER_ID)
        mock_get_order_runs.assert_called_with(
            NONE_TOKEN_HEADERS, DUMMY_KITCHEN, DUMMY_ORDER_ID, datakitchen_url=DUMMY_URL
        )
