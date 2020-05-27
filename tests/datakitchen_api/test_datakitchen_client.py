from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError

from dkutils.constants import COMPLETED_SERVING, PLANNED_SERVING
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
DUMMY_ORDER_RUN_ID = 'dummy_order_run_id'


class MockResponse:

    def __init__(self, raise_error=False, text=None, json=None):
        self._raise_error = raise_error
        self._text = text
        self._json = json

    @property
    def text(self):
        return self._text

    def raise_for_status(self):
        if self._raise_error:
            raise HTTPError('Failed API Call')

    def json(self):
        return self._json


class TestDataKitchenClient(TestCase):

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_setters(self, _):
        dk_client = DataKitchenClient(
            DUMMY_USERNAME,
            DUMMY_PASSWORD,
            base_url=DUMMY_URL,
            kitchen='kitchen',
            recipe='recipe',
            variation='variation'
        )
        self.assertEqual(dk_client.kitchen, 'kitchen')
        self.assertEqual(dk_client.recipe, 'recipe')
        self.assertEqual(dk_client.variation, 'variation')
        self.assertEqual(dk_client.set_kitchen(DUMMY_KITCHEN).kitchen, DUMMY_KITCHEN)
        self.assertEqual(dk_client.set_recipe(DUMMY_RECIPE).recipe, DUMMY_RECIPE)
        self.assertEqual(dk_client.set_variation(DUMMY_VARIATION).variation, DUMMY_VARIATION)
        dk_client.kitchen = 'kitchen'
        dk_client.recipe = 'recipe'
        dk_client.variation = 'variation'
        self.assertEqual(dk_client.kitchen, 'kitchen')
        self.assertEqual(dk_client.recipe, 'recipe')
        self.assertEqual(dk_client.variation, 'variation')

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_refresh_token(self, mock_post, mock_get):
        mock_get.return_value.raise_for_status.side_effect = HTTPError('Failed API Call')
        mock_post.return_value.text = DUMMY_AUTH_TOKEN
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        mock_get.assert_called_with(f'{DUMMY_URL}/v2/validatetoken', headers=None)
        mock_post.assert_called_with(f'{DUMMY_URL}/v2/login', data=DUMMY_CREDENTIALS)
        self.assertEqual(dk_client._headers, DUMMY_HEADERS)
        self.assertEqual(dk_client._token, DUMMY_AUTH_TOKEN)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_with_kitchen(self, _):
        dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL, kitchen=DUMMY_KITCHEN
        )
        self.assertEqual(dk_client._kitchen, DUMMY_KITCHEN)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_with_recipe(self, _):
        dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL, recipe=DUMMY_RECIPE
        )
        self.assertEqual(dk_client._recipe, DUMMY_RECIPE)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_with_variation(self, _):
        dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL, variation=DUMMY_VARIATION
        )
        self.assertEqual(dk_client._variation, DUMMY_VARIATION)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_missing_attributes(self, _):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError):
            dk_client.create_order()

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_order(self, _, mock_put):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        response_json = {
            "order_id": "abd8c538-705d-11ea-99d3-2699c9f5d2a0",
            "variable_overrides": {},
            "status": "success"
        }
        mock_put.return_value = MockResponse(json=response_json)
        response = dk_client.create_order()
        self.assertEqual(response.json(), response_json)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_order_raise_error(self, _, mock_put):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        mock_put.return_value = MockResponse(raise_error=True)
        with self.assertRaises(HTTPError):
            dk_client.create_order()

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_order_no_kitchen(self, _, mock_put):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        with self.assertRaises(ValueError):
            dk_client.create_order()

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_order_no_recipe(self, _, mock_put):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.variation = DUMMY_VARIATION
        with self.assertRaises(ValueError):
            dk_client.create_order()

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_order_no_variation(self, _, mock_put):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.recipe = DUMMY_RECIPE
        with self.assertRaises(ValueError):
            dk_client.create_order()

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_resume_order_run(self, _, mock_put):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        response_json = {
            "order_id": "abd8c538-705d-11ea-99d3-2699c9f5d2a0",
            "variable_overrides": {}
        }
        mock_put.return_value = MockResponse(json=response_json)
        response = dk_client.resume_order_run(DUMMY_ORDER_RUN_ID)
        self.assertEqual(response.json(), response_json)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_resume_order_run_raise_error(self, _, mock_put):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        mock_put.return_value = MockResponse(raise_error=True)
        with self.assertRaises(HTTPError):
            dk_client.resume_order_run(DUMMY_ORDER_RUN_ID)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_resume_order_run_no_kitchen(self, _, mock_put):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError):
            dk_client.resume_order_run(DUMMY_ORDER_RUN_ID)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_runs(self, _, mock_get):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        response_json = {
            "servings": [{
                "order_id": "71d8a966-38e0-11ea-8cf9-a6bbea194887",
                "status": "COMPLETED_SERVING",
                "orderrun_status": "OrderRun Completed",
                "hid": "a8978ddc-83c7-11ea-88ba-9a815c325cee",
                "variation_name": "dk_agent_checker_run_hourly",
                "timings": {
                    "start-time": 1587470413845,
                    "end-time": 1587470432441,
                    "duration": 18596
                }
            }]
        }
        mock_get.return_value = MockResponse(json=response_json)
        order_runs = dk_client.get_order_runs(DUMMY_ORDER_ID)
        self.assertEqual(order_runs, response_json['servings'])

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_runs_raise_error(self, _, mock_get):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        mock_get.return_value = MockResponse(raise_error=True)
        self.assertIsNone(dk_client.get_order_runs(DUMMY_ORDER_ID))

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_runs_no_kitchen(self, _, mock_get):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError):
            dk_client.get_order_runs(DUMMY_ORDER_ID)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_run_details(self, _, mock_post):
        response_json = {
            "repo":
                "au",
            "customer":
                "DKAutodesk",
            "kitchenname":
                "Add_Real_Data_and_Infrastructure",
            "orders": [{
                "order_id": "ca789c92-8bb6-11ea-883f-46ee3c6afcbf",
            }],
            "servings": [{
                "order_id": "ca789c92-8bb6-11ea-883f-46ee3c6afcbf",
                "hid": "cd463d80-8bb6-11ea-97c5-8a10ccb96113",
                "recipe_id": "ce7b696e-8bb6-11ea-97c5-8a10ccb96113",
                "status": "SERVING_ERROR",
                "run_time_variables": {
                    "CAT": "CLS",
                    "RecipeName": "Sub_Workflow",
                }
            }]
        }

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        mock_post.return_value = MockResponse(json=response_json)
        order_run_details = dk_client.get_order_run_details(DUMMY_ORDER_RUN_ID)
        self.assertEqual(order_run_details, response_json['servings'][0])

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_run_details_raise_error(self, _, mock_post):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        mock_post.return_value = MockResponse(raise_error=True)
        with self.assertRaises(HTTPError):
            dk_client.get_order_run_details(DUMMY_ORDER_RUN_ID)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_run_details_no_kitchen(self, _, mock_post):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError):
            dk_client.get_order_run_details(DUMMY_ORDER_RUN_ID)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_run_status(self, _, mock_post):
        response_json = {
            "repo":
                "au",
            "customer":
                "DKAutodesk",
            "kitchenname":
                "Add_Real_Data_and_Infrastructure",
            "orders": [{
                "order_id": "ca789c92-8bb6-11ea-883f-46ee3c6afcbf",
            }],
            "servings": [{
                "order_id": "ca789c92-8bb6-11ea-883f-46ee3c6afcbf",
                "hid": "cd463d80-8bb6-11ea-97c5-8a10ccb96113",
                "recipe_id": "ce7b696e-8bb6-11ea-97c5-8a10ccb96113",
                "status": "SERVING_ERROR",
                "run_time_variables": {
                    "CAT": "CLS",
                    "RecipeName": "Sub_Workflow",
                }
            }]
        }

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        mock_post.return_value = MockResponse(json=response_json)
        order_run_details = dk_client.get_order_run_status(DUMMY_ORDER_RUN_ID)
        self.assertEqual(order_run_details, response_json['servings'][0]['status'])

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_run_status_raise_error(self, _, mock_post):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        mock_post.return_value = MockResponse(raise_error=True)
        self.assertIsNone(dk_client.get_order_run_status(DUMMY_ORDER_RUN_ID))

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_run_status_no_kitchen(self, _, mock_post):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError):
            dk_client.get_order_run_status(DUMMY_ORDER_RUN_ID)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_monitor_order_run(self, _, mock_post):
        mock_post.side_effect = [
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
            MockResponse(json={'servings': [{
                'status': COMPLETED_SERVING
            }]}),
        ]
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        order_run_status = dk_client.monitor_order_run(1, 2, DUMMY_ORDER_RUN_ID)
        self.assertEqual(order_run_status, COMPLETED_SERVING)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_monitor_order_run_timeout(self, _, mock_post):
        mock_post.side_effect = [
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
        ]
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        order_run_status = dk_client.monitor_order_run(1, 2, DUMMY_ORDER_RUN_ID)
        self.assertIsNone(order_run_status)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_monitor_order_runs(self, _, mock_post):
        mock_post.side_effect = [
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
            MockResponse(json={'servings': [{
                'status': COMPLETED_SERVING
            }]}),
            MockResponse(json={'servings': [{
                'status': COMPLETED_SERVING
            }]}),
        ]
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        order_run_ids = {DUMMY_ORDER_RUN_ID: DUMMY_KITCHEN, 'Foo': 'Bar'}
        order_run_statuses = dk_client.monitor_order_runs(1, 2, order_run_ids)
        expected_statuses = {DUMMY_ORDER_RUN_ID: COMPLETED_SERVING, 'Foo': COMPLETED_SERVING}
        self.assertEqual(order_run_statuses, expected_statuses)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_monitor_order_runs_timeout(self, _, mock_post):
        mock_post.side_effect = [
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
            MockResponse(json={'servings': [{
                'status': PLANNED_SERVING
            }]}),
        ]
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)

        order_run_ids = {DUMMY_ORDER_RUN_ID: DUMMY_KITCHEN, 'Foo': 'Bar'}
        order_run_statuses = dk_client.monitor_order_runs(1, 2, order_run_ids)
        expected_statuses = {DUMMY_ORDER_RUN_ID: None, 'Foo': None}
        self.assertEqual(order_run_statuses, expected_statuses)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_update_kitchen_vault(self, _, mock_post):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        response_json = {'test_update_kitchen_vault': 1}
        mock_post.return_value = MockResponse(json=response_json)
        response = dk_client.update_kitchen_vault('Implementation/dev', 'vault_token')
        self.assertEqual(response.json(), response_json)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_update_kitchen_vault_raise_error(self, _, mock_post):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        response_json = {'test_update_kitchen_vault': 1}
        mock_post.return_value = MockResponse(raise_error=True, json=response_json)
        with self.assertRaises(HTTPError):
            dk_client.update_kitchen_vault('Implementation/dev', 'vault_token')
