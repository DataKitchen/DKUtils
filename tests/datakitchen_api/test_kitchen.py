from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError

from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient
from dkutils.datakitchen_api.kitchen import Kitchen
from .test_datakitchen_client import (
    DUMMY_USERNAME, DUMMY_PASSWORD, DUMMY_URL, DUMMY_KITCHEN, MockResponse
)

KITCHEN_SETTINGS = {
    'kitchen': {
        '_hid': '6d225508-bb78-11ec-9b66-26e9c463e6eb',
        'created_time': 1649888644307,
        'creator_user': 'ddicara+im@datakitchen.io',
        'customer': 'Implementation',
        'description': '',
        'git_name': 'im',
        'git_org': 'DKImplementation',
        'kitchen-roles': {
            'Admin': ['ddicara+im@datakitchen.io'],
            'Developer': ['atiwari+im@datakitchen.io']
        },
        'kitchen-staff': ['atiwari+im@datakitchen.io', 'ddicara+im@datakitchen.io'],
        'name': 'foo',
        'parent-kitchen': 'IM_Development',
        'recipeoverrides': {
            'gpcConfig': {
                'image_repo': 'dk_general_purpose_container',
                'image_tag': 'latest',
                'namespace': 'datakitchenprod',
                'password': '#{vault://dockerhub/password}',
                'username': '#{vault://dockerhub/username}'
            },
        },
        'recipes': ['CICD_DKUtils', 'Utility_Toggl'],
        'settings': {
            'agile-tools': None,
            'alerts': {
                'orderrunError': ['ddicara+im@datakitchen.io'],
                'orderrunOverDuration': None,
                'orderrunStart': None,
                'orderrunSuccess': ['ddicara@gmail.com', 'dandicara@gmail.com'],
                'orderrunWarning': None,
                'py/object': 'DKModules.DKKitchen.DKAlerts'
            }
        }
    }
}

ALERTS = {
    'Failure': ['ddicara+im@datakitchen.io'],
    'OverDuration': None,
    'Start': None,
    'Success': ['ddicara@gmail.com', 'dandicara@gmail.com'],
    'Warning': None
}


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
        Kitchen(self.dk_client, 'foo').delete()
        mock_delete.assert_called_with(f'{DUMMY_URL}/v2/kitchen/delete/foo', headers=None, json={})

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.delete')
    def test_delete_kitchen_raise_exception(self, mock_delete, _):
        mock_delete.return_value = MockResponse(raise_error=True)
        k = Kitchen(self.dk_client, 'foo')
        with self.assertRaises(HTTPError):
            k.delete()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_settings(self, mock_get, _):
        Kitchen(self.dk_client, 'foo')._get_settings()
        mock_get.assert_called_with(f'{DUMMY_URL}/v2/kitchen/foo', headers=None, json={})

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_settings_raise_exception(self, mock_get, _):
        mock_get.return_value = MockResponse(raise_error=True)
        with self.assertRaises(HTTPError):
            Kitchen(self.dk_client, 'foo')._get_settings()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_update_settings(self, mock_post, _):
        Kitchen(self.dk_client, 'foo')._update_settings(deepcopy(KITCHEN_SETTINGS))
        exp_json = {'kitchen.json': KITCHEN_SETTINGS['kitchen']}
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/kitchen/update/foo', headers=None, json=exp_json
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_update_settings_raise_exception(self, mock_post, _):
        mock_post.return_value = MockResponse(raise_error=True)
        with self.assertRaises(HTTPError):
            Kitchen(self.dk_client, 'foo')._update_settings(deepcopy(KITCHEN_SETTINGS))

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_alerts(self, mock_get, _):
        mock_get.return_value = MockResponse(json=deepcopy(KITCHEN_SETTINGS))
        alerts = Kitchen(self.dk_client, 'foo').get_alerts()
        self.assertEqual(alerts, ALERTS)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_add_alerts(self, mock_get, mock_post, _):
        exp_json = deepcopy(KITCHEN_SETTINGS)
        exp_json['kitchen']['settings']['alerts']['orderrunOverDuration'] = ['foo@gmail.com']
        exp_json['kitchen.json'] = exp_json['kitchen']
        del exp_json['kitchen']
        new_alerts = {'OverDuration': ['foo@gmail.com']}

        mock_get.return_value = MockResponse(json=deepcopy(KITCHEN_SETTINGS))
        Kitchen(self.dk_client, 'foo').add_alerts(new_alerts)
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/kitchen/update/foo', headers=None, json=exp_json
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_delete_alerts(self, mock_get, mock_post, _):
        exp_json = deepcopy(KITCHEN_SETTINGS)
        exp_json['kitchen']['settings']['alerts']['orderrunSuccess'] = ['ddicara@gmail.com']
        exp_json['kitchen.json'] = exp_json['kitchen']
        del exp_json['kitchen']
        delete_alerts = {'Success': ['dandicara@gmail.com']}

        mock_get.return_value = MockResponse(json=deepcopy(KITCHEN_SETTINGS))
        Kitchen(self.dk_client, 'foo').delete_alerts(delete_alerts)
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/kitchen/update/foo', headers=None, json=exp_json
        )
