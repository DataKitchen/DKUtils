from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError
from uuid import UUID, uuid1

from dkutils.constants import API_GET
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
        "kitchen-roles": {
            "user1@email.com": "Admin",
            "user2@email.com": "Admin",
            "user3@email.com": "Developer",
            "User4@EMAIL.com": "Guest"
        },
        "kitchen-staff": [
            "user1@email.com", "user2@email.com", "user3@email.com", "User4@EMAIL.com"
        ],
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

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_parent_name(self, mock_request):
        mock_request.return_value = MockResponse(json=KITCHEN_SETTINGS)
        parent_name = Kitchen(self.dk_client, 'foo').parent_name
        mock_request.assert_called_with(API_GET, 'kitchen', 'foo')
        self.assertEqual(parent_name, KITCHEN_SETTINGS['kitchen']['parent-kitchen'])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_is_ingredient_true(self, mock_request):
        mock_request.return_value = MockResponse(json=KITCHEN_SETTINGS)
        ingredient_kitchen_name = KITCHEN_SETTINGS['kitchen']['parent-kitchen']
        ingredient_kitchen_name += f'_{UUID(str(uuid1())).hex}'
        self.assertTrue(Kitchen(self.dk_client, ingredient_kitchen_name).is_ingredient())

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_is_ingredient_false(self, mock_request):
        mock_request.return_value = MockResponse(json=KITCHEN_SETTINGS)
        self.assertFalse(Kitchen(self.dk_client, 'foo').is_ingredient())

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

    def test_get_roles_with_settings(self):
        expected = {
            "Admin": ["user1@email.com", "user2@email.com"],
            "Developer": ["user3@email.com"],
            "Guest": ["User4@EMAIL.com"]
        }
        roles = Kitchen(self.dk_client, 'foo')._get_roles(settings=KITCHEN_SETTINGS)
        self.assertEqual(roles, expected)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_roles_without_settings(self, mock_get):
        expected = {
            "Admin": ["user1@email.com", "user2@email.com"],
            "Developer": ["user3@email.com"],
            "Guest": ["User4@EMAIL.com"]
        }
        mock_get.return_value = MockResponse(json=KITCHEN_SETTINGS)
        roles = Kitchen(self.dk_client, 'foo')._get_roles()
        self.assertEqual(roles, expected)

    def test_get_staff_set_with_settings(self):
        roles = Kitchen(self.dk_client, 'foo')._get_staff_set(settings=KITCHEN_SETTINGS)
        self.assertEqual(roles, set(KITCHEN_SETTINGS['kitchen']['kitchen-staff']))

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_staff_set_with_no_settings(self, mock_get):
        mock_get.return_value = MockResponse(json=KITCHEN_SETTINGS)
        roles = Kitchen(self.dk_client, 'foo')._get_staff_set()
        self.assertEqual(roles, set(KITCHEN_SETTINGS['kitchen']['kitchen-staff']))

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_ensure_admin(self, mock_get):
        settings = deepcopy(KITCHEN_SETTINGS)
        settings['kitchen']['kitchen-roles'][DUMMY_USERNAME] = 'Admin'
        mock_get.return_value = MockResponse(json=settings)
        Kitchen(self.dk_client, 'foo')._ensure_admin()

    def test_ensure_admin_with_settings(self):
        settings = deepcopy(KITCHEN_SETTINGS)
        settings['kitchen']['kitchen-roles'][DUMMY_USERNAME] = 'Admin'
        Kitchen(self.dk_client, 'foo')._ensure_admin(settings=settings)

    def test_ensure_admin_with_roles(self):
        kitchen = Kitchen(self.dk_client, 'foo')
        roles = deepcopy(kitchen._get_roles(settings=KITCHEN_SETTINGS))
        roles['Admin'].append(DUMMY_USERNAME)
        kitchen._ensure_admin(roles=roles)

    def test_ensure_admin_error(self):
        with self.assertRaises(PermissionError):
            Kitchen(self.dk_client, 'foo')._ensure_admin(settings=KITCHEN_SETTINGS)

    def test_ensure_disjoint(self):
        lists = [[1, 2], [3, 4], [5, 6]]
        self.assertTrue(Kitchen(self.dk_client, 'foo')._ensure_disjoint(lists))

    def test_ensure_disjoint_fail(self):
        lists = [[1, 2], [3, 4], [4, 6]]
        self.assertFalse(Kitchen(self.dk_client, 'foo')._ensure_disjoint(lists))

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_staff(self, mock_get):
        expected = {
            "Admin": ["user1@email.com", "user2@email.com"],
            "Developer": ["user3@email.com"],
            "Guest": ["User4@EMAIL.com"]
        }
        mock_get.return_value = MockResponse(json=KITCHEN_SETTINGS)
        staff = Kitchen(self.dk_client, 'foo').get_staff()
        self.assertEqual(staff, expected)

    @patch('dkutils.datakitchen_api.kitchen.Kitchen._ensure_admin')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_delete_staff_with_existing_user(self, mock_post, mock_get, _):
        mock_get.return_value = MockResponse(json=deepcopy(KITCHEN_SETTINGS))
        Kitchen(self.dk_client, 'foo').delete_staff(['user3@email.com'])
        exp_settings = {'kitchen.json': deepcopy(KITCHEN_SETTINGS['kitchen'])}
        del exp_settings['kitchen.json']['kitchen-roles']['user3@email.com']
        current_staff = set(exp_settings['kitchen.json']['kitchen-staff'])
        new_staff = {'user3@email.com'}
        staff = list(current_staff - new_staff)
        exp_settings['kitchen.json']['kitchen-staff'] = staff
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/kitchen/update/foo', headers=None, json=exp_settings
        )

    @patch('dkutils.datakitchen_api.kitchen.Kitchen._ensure_admin')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_delete_staff_with_non_existing_user(self, mock_post, mock_get, _):
        mock_get.return_value = MockResponse(json=deepcopy(KITCHEN_SETTINGS))

        kitchen = Kitchen(self.dk_client, 'foo')
        with self.assertRaises(ValueError):
            kitchen.delete_staff(['non_existing_user@datakitchen.io'])

    @patch('dkutils.datakitchen_api.kitchen.Kitchen._ensure_admin')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_add_staff(self, mock_post, mock_get, _):
        mock_get.return_value = MockResponse(json=deepcopy(KITCHEN_SETTINGS))
        kitchen = Kitchen(self.dk_client, 'foo')
        kitchen.add_staff({'Developer': ['new_developer@datakitchen.io']})

        exp_settings = {'kitchen.json': deepcopy(KITCHEN_SETTINGS['kitchen'])}
        exp_settings['kitchen.json']['kitchen-roles']['new_developer@datakitchen.io'] = 'Developer'
        current_staff = set(exp_settings['kitchen.json']['kitchen-staff'])
        new_staff = {'new_developer@datakitchen.io'}
        staff = list(current_staff | new_staff)
        exp_settings['kitchen.json']['kitchen-staff'] = staff
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/kitchen/update/foo', headers=None, json=exp_settings
        )

    @patch('dkutils.datakitchen_api.kitchen.Kitchen._ensure_admin')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_update_staff(self, mock_post, mock_get, _):
        mock_get.return_value = MockResponse(json=deepcopy(KITCHEN_SETTINGS))
        Kitchen(self.dk_client, 'foo').update_staff({
            'Admin': ['User4@EMAIL.com'],
            'Developer': ['user1@email.com', 'user2@email.com'],
        })

        exp_settings = {'kitchen.json': deepcopy(KITCHEN_SETTINGS['kitchen'])}
        exp_settings['kitchen.json']['kitchen-roles']['user1@email.com'] = 'Developer'
        exp_settings['kitchen.json']['kitchen-roles']['user2@email.com'] = 'Developer'
        exp_settings['kitchen.json']['kitchen-roles']['User4@EMAIL.com'] = 'Admin'
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/kitchen/update/foo', headers=None, json=exp_settings
        )
