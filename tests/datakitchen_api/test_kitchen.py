from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError

from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient
from dkutils.datakitchen_api.kitchen import Kitchen
from .test_datakitchen_client import (
    DUMMY_USERNAME, DUMMY_PASSWORD, DUMMY_URL, DUMMY_KITCHEN, MockResponse
)


class TestKitchen(TestCase):

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def setUp(self, _):
        self.dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, kitchen=DUMMY_KITCHEN, base_url=DUMMY_URL
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    def test_create_kitchen(self, mock_put, _):
        Kitchen.create(self.dk_client, 'parent_kitchen', 'new_kitchen', 'description')
        mock_put.assert_called_with(
            f'{DUMMY_URL}/v2/kitchen/create/parent_kitchen/new_kitchen',
            headers=None,
            json={'description': 'description'}
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    def test_create_kitchen_raise_exception(self, mock_put, _):
        mock_put.return_value = MockResponse(raise_error=True)
        with self.assertRaises(HTTPError):
            Kitchen.create(self.dk_client, 'parent_kitchen', 'new_kitchen', 'description')

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.delete')
    def test_delete_kitchen(self, mock_delete, _):
        k = Kitchen(self.dk_client, 'foo')
        k.delete()
        mock_delete.assert_called_with(f'{DUMMY_URL}/v2/kitchen/delete/foo', headers=None, json={})

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.delete')
    def test_delete_kitchen_raise_exception(self, mock_delete, _):
        mock_delete.return_value = MockResponse(raise_error=True)
        k = Kitchen(self.dk_client, 'foo')
        with self.assertRaises(HTTPError):
            k.delete()
