from unittest import TestCase
from unittest.mock import patch

from dkutils.constants import DEFAULT_VAULT_URL, GLOBAL
from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient
from dkutils.datakitchen_api.vault import Vault
from .test_datakitchen_client import (
    DUMMY_USERNAME, DUMMY_PASSWORD, DUMMY_URL, DUMMY_KITCHEN, MockResponse
)

SECRET_PATH = 'dockerhub/username'
SECRET_VALUE = 'foo@datakitchen.io'

ERROR_KITCHEN = 'error_kitchen'
VAULT_CONFIG = {
    'config': {
        '**__GLOBAL__**': {
            'prefix': '',
            'private': False,
            'service': 'default',
            'url': ''
        },
        DUMMY_KITCHEN: {
            'inheritable': True,
            'prefix': 'Customer/dummy',
            'private': False,
            'service': 'custom',
            'url': 'https://vault2.datakitchen.io:8200'
        }
    }
}

SECRETS = {
    '**__GLOBAL__**': {
        'error': False,
        'list': ['vault://useradmin/password', 'vault://useradmin/username']
    },
    DUMMY_KITCHEN: {
        'error':
            False,
        'list': [
            'vault://bigquery/json_private_key',
            'vault://dockerhub/password',
            'vault://dockerhub/username',
        ]
    },
    ERROR_KITCHEN: {
        'error': True,
        'error-message':
            'Kitchen error_kitchen was '
            'not found in the database or the '
            'user does not have access rights.'
    }
}


class TestVault(TestCase):

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def setUp(self, _):
        self.client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        self.vault = Vault(self.client, DUMMY_KITCHEN)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_get_global_config(self, mock_request):
        mock_request.return_value = MockResponse(json=VAULT_CONFIG)
        config = self.vault.get_config(is_global=True)
        self.assertEqual(config, VAULT_CONFIG['config'][GLOBAL])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_get_kitchen_config(self, mock_request):
        mock_request.return_value = MockResponse(json=VAULT_CONFIG)
        config = self.vault.get_config()
        self.assertEqual(config, VAULT_CONFIG['config'][DUMMY_KITCHEN])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.update_kitchen_vault')
    def test_update_config(self, update_kitchen_vault):
        self.vault.update_config('prefix', 'token')
        update_kitchen_vault.assert_called_with(
            'prefix', 'token', vault_url=DEFAULT_VAULT_URL, private=False, inheritable=True
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_get_global_secrets(self, mock_request):
        mock_request.return_value = MockResponse(json=SECRETS)
        secrets = self.vault.get_secrets(is_global=True)
        self.assertEqual(secrets, SECRETS[GLOBAL]['list'])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_get_kitchen_secrets(self, mock_request):
        mock_request.return_value = MockResponse(json=SECRETS)
        secrets = self.vault.get_secrets()
        self.assertEqual(secrets, SECRETS[DUMMY_KITCHEN]['list'])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_get_error_kitchen_secrets(self, mock_request):
        mock_request.return_value = MockResponse(json=SECRETS)
        vault = Vault(self.client, ERROR_KITCHEN)
        with self.assertRaises(ValueError) as cm:
            vault.get_secrets()
        expected_error = 'Error retrieving secrets: Kitchen error_kitchen was not found in the ' \
                'database or the user does not have access rights.'
        self.assertEqual(expected_error, cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_update_or_add_kitchen_secret(self, _, mock_post):
        self.vault.update_or_add_secret(SECRET_PATH, SECRET_VALUE)
        kwargs = {'kitchen': DUMMY_KITCHEN, 'value': SECRET_VALUE}
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/secret/{SECRET_PATH}', headers=None, json=kwargs
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_update_or_add_global_secret(self, _, mock_post):
        self.vault.update_or_add_secret(SECRET_PATH, SECRET_VALUE, is_global=True)
        kwargs = {'kitchen': None, 'value': SECRET_VALUE}
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/secret/{SECRET_PATH}', headers=None, json=kwargs
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.delete')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_delete_kitchen_secret(self, _, mock_delete):
        self.vault.delete_secret(SECRET_PATH)
        kwargs = {'kitchen': DUMMY_KITCHEN}
        mock_delete.assert_called_with(
            f'{DUMMY_URL}/v2/secret/{SECRET_PATH}', headers=None, json=kwargs
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.delete')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_delete_global_secret(self, _, mock_delete):
        self.vault.delete_secret(SECRET_PATH, is_global=True)
        kwargs = {'kitchen': None}
        mock_delete.assert_called_with(
            f'{DUMMY_URL}/v2/secret/{SECRET_PATH}', headers=None, json=kwargs
        )
