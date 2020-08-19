import json
import os
from unittest import TestCase
from unittest.mock import patch, call, mock_open

from requests.exceptions import HTTPError

from dkutils.constants import (
    COMPLETED_SERVING, KITCHEN, ORDER_ID, ORDER_RUN_ID, ORDER_RUN_STATUS, PARAMETERS,
    PLANNED_SERVING, RECIPE, VARIATION, PARENT_KITCHEN
)
from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient, create_using_context
from dkutils.datakitchen_api.datetime_utils import get_utc_timestamp
from dkutils.dictionary_comparator import DictionaryComparator

DUMMY_PORT = "443"
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
DUMMY_ORDER_ID2 = 'dummy_order_id2'
DUMMY_ORDER_RUN_ID = 'dummy_order_run_id'
DUMMY_ORDER_RUN_ID2 = 'dummy_order_run_id2'
GET_RECIPES_URL = f'{DUMMY_URL}/v2/recipe/variations/listfromorders/{DUMMY_KITCHEN}'
LIST_KITCHEN_URL = f'{DUMMY_URL}/v2/kitchen/list'
KITCHEN_STAFF = "kitchen-staff"
RECIPE_OVERRIDES = "recipeoverrides"
JSON_PROFILE = {
    "dk-cloud-ip": DUMMY_URL,
    "dk-cloud-port": DUMMY_PORT,
    "dk-cloud-username": DUMMY_USERNAME,
    "dk-cloud-password": DUMMY_PASSWORD
}
RECIPES = {DUMMY_RECIPE: [DUMMY_VARIATION]}


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
    def setUp(self, _):
        self.dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, kitchen=DUMMY_KITCHEN, base_url=DUMMY_URL
        )

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
        self.assertFalse(dk_client._valid_attributes)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_refresh_token(self, mock_post, mock_get):
        mock_get.return_value.raise_for_status.side_effect = HTTPError('Failed API Call')
        mock_post.return_value.text = DUMMY_AUTH_TOKEN
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        mock_get.assert_called_with(f'{DUMMY_URL}/v2/validatetoken', headers=None, json={})
        mock_post.assert_called_with(f'{DUMMY_URL}/v2/login', data=DUMMY_CREDENTIALS, headers=None)
        self.assertEqual(dk_client._headers, DUMMY_HEADERS)
        self.assertEqual(dk_client._token, DUMMY_AUTH_TOKEN)

    def test_with_kitchen(self):
        self.assertEqual(self.dk_client._kitchen, DUMMY_KITCHEN)

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

    def test_missing_attributes(self):
        with self.assertRaises(ValueError) as cm:
            self.dk_client.create_order()
        self.assertEqual('Undefined attributes: recipe,variation', cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._ensure_attributes')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_order(self, _, mock_put, mock_ensure_attributes):
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
        mock_ensure_attributes.assert_called_once_with(KITCHEN, RECIPE, VARIATION)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._ensure_attributes')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_order_raise_error(self, _, mock_put, mock_ensure_attributes):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        mock_put.return_value = MockResponse(raise_error=True)
        with self.assertRaises(HTTPError):
            dk_client.create_order()
        mock_ensure_attributes.assert_called()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._ensure_attributes')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_order_when_attributes_not_valid(self, _, mock_put, mock_ensure_attributes):
        mock_ensure_attributes.side_effect = ValueError("Bad")
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        with self.assertRaises(ValueError) as cm:
            dk_client.create_order()
        self.assertEqual(mock_ensure_attributes.side_effect, cm.exception)
        mock_ensure_attributes.assert_called_once_with(KITCHEN, RECIPE, VARIATION)
        mock_put.assert_not_called()

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
        with self.assertRaises(ValueError) as cm:
            dk_client.resume_order_run(DUMMY_ORDER_RUN_ID)
        self.assertEqual('Undefined attributes: kitchen', cm.exception.args[0])

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
        with self.assertRaises(ValueError) as cm:
            dk_client.get_order_runs(DUMMY_ORDER_ID)
        self.assertEqual('Undefined attributes: kitchen', cm.exception.args[0])

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
        with self.assertRaises(ValueError) as cm:
            dk_client.get_order_run_details(DUMMY_ORDER_RUN_ID)
        self.assertEqual('Undefined attributes: kitchen', cm.exception.args[0])

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
        with self.assertRaises(ValueError) as cm:
            dk_client.get_order_run_status(DUMMY_ORDER_RUN_ID)
        self.assertEqual('Undefined attributes: kitchen', cm.exception.args[0])

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

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._ensure_attributes')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_and_monitor_order_runs(
        self, _, mock_put, mock_get, mock_post, mock_ensure_attributes
    ):
        orders_details = [
            {
                KITCHEN: DUMMY_KITCHEN,
                RECIPE: DUMMY_RECIPE,
                VARIATION: DUMMY_VARIATION,
            },
        ]
        mock_put.side_effect = [MockResponse(json={ORDER_ID: DUMMY_ORDER_ID})]
        mock_get.side_effect = [MockResponse(json={'servings': [{'hid': DUMMY_ORDER_RUN_ID}]})]
        mock_post.side_effect = [MockResponse(json={'servings': [{'status': COMPLETED_SERVING}]})]

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        results = dk_client.create_and_monitor_orders(orders_details, 1, 2)

        orders_details[0][ORDER_ID] = DUMMY_ORDER_ID
        orders_details[0][ORDER_RUN_ID] = DUMMY_ORDER_RUN_ID
        orders_details[0][ORDER_RUN_STATUS] = COMPLETED_SERVING
        self.assertEqual(results[0], orders_details)
        self.assertFalse(results[1])
        self.assertFalse(results[2])
        mock_ensure_attributes.assert_called()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._ensure_attributes')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_create_and_monitor_order_runs_timeout(
        self, _, mock_put, mock_get, mock_post, mock_validate
    ):
        orders_details = [
            {
                KITCHEN: DUMMY_KITCHEN,
                RECIPE: DUMMY_RECIPE,
                VARIATION: DUMMY_VARIATION,
            },
        ]
        mock_put.side_effect = [MockResponse(json={ORDER_ID: DUMMY_ORDER_ID})]
        mock_get.side_effect = [MockResponse(json={'servings': [{'hid': DUMMY_ORDER_RUN_ID}]})]
        mock_post.side_effect = [MockResponse(json={'servings': [{'status': PLANNED_SERVING}]})]

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        results = dk_client.create_and_monitor_orders(orders_details, 1, 2)

        orders_details[0][ORDER_ID] = DUMMY_ORDER_ID
        orders_details[0][ORDER_RUN_ID] = DUMMY_ORDER_RUN_ID
        orders_details[0][ORDER_RUN_STATUS] = PLANNED_SERVING
        self.assertFalse(results[0])
        self.assertEqual(results[1], orders_details)
        self.assertFalse(results[2])
        mock_validate.assert_called()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._ensure_attributes')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def _ensure_attributestest_create_and_monitor_order_runs_multiple(
        self, _, mock_put, mock_get, mock_post, mock_ensure_attributes
    ):
        orders_details = [
            {
                KITCHEN: DUMMY_KITCHEN,
                RECIPE: DUMMY_RECIPE,
                VARIATION: DUMMY_VARIATION,
                PARAMETERS: {
                    'DT': '20200501'
                }
            },
            {
                KITCHEN: DUMMY_KITCHEN,
                RECIPE: DUMMY_RECIPE,
                VARIATION: DUMMY_VARIATION,
                PARAMETERS: {
                    'DT': '20200502'
                }
            },
        ]
        mock_put.side_effect = [
            MockResponse(json={ORDER_ID: DUMMY_ORDER_ID}),
            MockResponse(json={ORDER_ID: DUMMY_ORDER_ID2}),
        ]
        mock_get.side_effect = [MockResponse(json={'servings': [{'hid': DUMMY_ORDER_RUN_ID}]})]
        mock_post.side_effect = [MockResponse(json={'servings': [{'status': COMPLETED_SERVING}]})]

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        results = dk_client.create_and_monitor_orders(orders_details, 1, 2, max_concurrent=1)

        orders_details[0][ORDER_ID] = DUMMY_ORDER_ID
        orders_details[0][ORDER_RUN_ID] = DUMMY_ORDER_RUN_ID
        orders_details[0][ORDER_RUN_STATUS] = COMPLETED_SERVING
        orders_details[1][ORDER_ID] = DUMMY_ORDER_ID2
        orders_details[1][ORDER_RUN_ID] = None
        orders_details[1][ORDER_RUN_STATUS] = None
        self.assertEqual(results[0], [orders_details[0]])
        self.assertEqual(results[1], [orders_details[1]])
        self.assertFalse(results[2])
        mock_ensure_attributes.assert_called()

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_resume_and_monitor_order_runs(self, _, mock_put, mock_get, mock_post):
        orders_details = [
            {
                KITCHEN: DUMMY_KITCHEN,
                ORDER_RUN_ID: DUMMY_ORDER_RUN_ID,
            },
        ]
        mock_put.side_effect = [
            MockResponse(json={ORDER_ID: DUMMY_ORDER_ID}),
            MockResponse(json={ORDER_ID: DUMMY_ORDER_ID}),
        ]
        mock_get.side_effect = [
            MockResponse(
                json={
                    'servings': [{
                        'hid': DUMMY_ORDER_RUN_ID,
                        'timings': {
                            'start-time': get_utc_timestamp() + 60 * 1000
                        }
                    }]
                }
            )
        ]
        mock_post.side_effect = [MockResponse(json={'servings': [{'status': COMPLETED_SERVING}]})]

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        results = dk_client.resume_and_monitor_orders(orders_details, 1, 2)

        orders_details[0][ORDER_ID] = DUMMY_ORDER_ID
        orders_details[0][ORDER_RUN_ID] = DUMMY_ORDER_RUN_ID
        orders_details[0][ORDER_RUN_STATUS] = COMPLETED_SERVING
        self.assertEqual(results[0], orders_details)
        self.assertFalse(results[1])
        self.assertFalse(results[2])

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_resume_and_monitor_order_runs_timeout(self, _, mock_put, mock_get, mock_post):
        orders_details = [
            {
                KITCHEN: DUMMY_KITCHEN,
                ORDER_RUN_ID: DUMMY_ORDER_RUN_ID,
            },
        ]
        mock_put.side_effect = [MockResponse(json={ORDER_ID: DUMMY_ORDER_ID})]
        mock_get.side_effect = [
            MockResponse(
                json={
                    'servings': [{
                        'hid': DUMMY_ORDER_RUN_ID,
                        'timings': {
                            'start-time': get_utc_timestamp() + 60 * 1000
                        }
                    }]
                }
            )
        ]
        mock_post.side_effect = [MockResponse(json={'servings': [{'status': PLANNED_SERVING}]})]

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        results = dk_client.resume_and_monitor_orders(orders_details, 1, 2)

        orders_details[0][ORDER_ID] = DUMMY_ORDER_ID
        orders_details[0][ORDER_RUN_ID] = DUMMY_ORDER_RUN_ID
        orders_details[0][ORDER_RUN_STATUS] = PLANNED_SERVING
        self.assertFalse(results[0])
        self.assertEqual(results[1], orders_details)
        self.assertFalse(results[2])

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.put')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_resume_and_monitor_order_runs_multiple(self, _, mock_put, mock_get, mock_post):
        orders_details = [
            {
                KITCHEN: DUMMY_KITCHEN,
                ORDER_RUN_ID: DUMMY_ORDER_RUN_ID,
            },
            {
                KITCHEN: DUMMY_KITCHEN,
                ORDER_RUN_ID: DUMMY_ORDER_RUN_ID2,
            },
        ]
        mock_put.side_effect = [
            MockResponse(json={ORDER_ID: DUMMY_ORDER_ID}),
            MockResponse(json={ORDER_ID: DUMMY_ORDER_ID2})
        ]
        mock_get.side_effect = [
            MockResponse(
                json={
                    'servings': [{
                        'hid': DUMMY_ORDER_RUN_ID,
                        'timings': {
                            'start-time': get_utc_timestamp() + 60 * 1000
                        }
                    }]
                }
            )
        ]
        mock_post.side_effect = [MockResponse(json={'servings': [{'status': COMPLETED_SERVING}]})]

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        results = dk_client.resume_and_monitor_orders(orders_details, 1, 2, max_concurrent=1)

        orders_details[0][ORDER_ID] = DUMMY_ORDER_ID
        orders_details[0][ORDER_RUN_ID] = DUMMY_ORDER_RUN_ID
        orders_details[0][ORDER_RUN_STATUS] = COMPLETED_SERVING
        orders_details[1][ORDER_ID] = DUMMY_ORDER_ID2
        orders_details[1][ORDER_RUN_ID] = None
        orders_details[1][ORDER_RUN_STATUS] = None
        self.assertEqual(results[0], [orders_details[0]])
        self.assertEqual(results[1], [orders_details[1]])
        self.assertFalse(results[2])

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

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_kitchen_info_when_kitchen_not_set_raises_value_error(self, _):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError) as cm:
            dk_client._get_kitchen_info()
        self.assertEqual('Undefined attributes: kitchen', cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_kitchen_info_when_no_kitchen_found_raises_value_error(self, mock_get):
        mock_get.return_value = MockResponse(json={'kitchens': []})
        with self.assertRaises(ValueError) as cm:
            self.dk_client._get_kitchen_info()
        self.assertEqual(
            f"No kitchen with the name: {DUMMY_KITCHEN} was found in the available kitchens",
            cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_kitchen_info_when_more_than_one_kitchen_found_raises_value_error(self, mock_get):
        mock_get.return_value = MockResponse(
            json={'kitchens': [{
                'name': DUMMY_KITCHEN
            }, {
                'name': DUMMY_KITCHEN
            }]}
        )
        with self.assertRaises(ValueError) as cm:
            self.dk_client._get_kitchen_info()
        self.assertEqual(
            f"More than 1 kitchen with the name: {DUMMY_KITCHEN} found in list of kitchens",
            cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_kitchen_info(self, _, mock_get):
        kitchen_info = {'_created': None, '_finished': False, 'name': DUMMY_KITCHEN}
        mock_get.return_value = MockResponse(
            json={'kitchens': [{
                'name': 'some_kitchen'
            }, kitchen_info]}
        )
        self.assertEqual(kitchen_info, self.dk_client._get_kitchen_info())
        mock_get.assert_called_once_with(LIST_KITCHEN_URL, headers=None, json={})

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_update_kitchen_when_kitchen_not_set_raises_value_error(self, _):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError):
            dk_client._update_kitchen({})

    def test_update_kitchen_when_kitchen_does_not_match_set_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            kitchen_name = 'bob'
            self.dk_client._update_kitchen({'name': kitchen_name})
        self.assertEqual(
            f'Name in kitchen_info: {kitchen_name} does not match current kitchen: {DUMMY_KITCHEN}',
            cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_update_kitchen(self, _, mock_post):
        kitchen_info = {"name": DUMMY_KITCHEN}
        self.dk_client._update_kitchen(kitchen_info)
        mock_post.assert_called_once_with(
            f'{DUMMY_URL}/v2/kitchen/update/{DUMMY_KITCHEN}',
            headers=None,
            json={'kitchen.json': kitchen_info}
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchen_info')
    def test_get_overrides(self, mock_get_kitchen_info):
        overrides = {"something": "blue"}
        mock_get_kitchen_info.return_value = {RECIPE_OVERRIDES: overrides}
        self.assertEqual(overrides, self.dk_client.get_overrides())
        mock_get_kitchen_info.assert_called_once_with()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchen_info')
    def test_get_overrides_when_override_names_contains_unknown_names_then_valueerror_is_raised(
        self, mock_get_kitchen_info
    ):
        overrides = {"something": "blue"}
        mock_get_kitchen_info.return_value = {RECIPE_OVERRIDES: overrides}
        overide_names = {'bobby'}
        with self.assertRaises(ValueError) as cm:
            self.dk_client.get_overrides(overide_names)
        self.assertEqual(
            f'The following overrides are not available in the kitchen: {overide_names}',
            cm.exception.args[0]
        )
        mock_get_kitchen_info.assert_called_once_with()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchen_info')
    def test_get_overrides_when_override_names_contains_subset_of_names(
        self, mock_get_kitchen_info
    ):
        existing_name = 'something'
        overrides = {'something': "penguin", "borrowed": "baseball", "blue": "skye"}
        mock_get_kitchen_info.return_value = {RECIPE_OVERRIDES: overrides}
        overide_names = {existing_name}
        expected_overrides = {
            key: value
            for (key, value) in overrides.items()
            if key == existing_name
        }
        self.assertEqual(expected_overrides, self.dk_client.get_overrides(overide_names))
        mock_get_kitchen_info.assert_called_once_with()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._update_kitchen')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchen_info')
    def test_update_overrides(self, mock_get_kitchen_info, mock_update_kitchen_info):
        kitchen_info_with_original_overrides = {
            "name": DUMMY_KITCHEN,
            RECIPE_OVERRIDES: {
                "something": "blue"
            }
        }
        new_overrides = {"something": "new"}
        kitchen_info_with_new_overrides = kitchen_info_with_original_overrides.copy()
        kitchen_info_with_new_overrides[RECIPE_OVERRIDES] = new_overrides
        mock_get_kitchen_info.return_value = kitchen_info_with_original_overrides
        self.dk_client.update_overrides(new_overrides)
        mock_get_kitchen_info.assert_called_once_with()
        mock_update_kitchen_info.assert_called_once_with(kitchen_info_with_new_overrides)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchens_info')
    def test_compare_overrides_when_non_existent_kitchen_raises_error(self, mock_get_kitchens_info):
        mock_get_kitchens_info.return_value = {DUMMY_KITCHEN: {"name": DUMMY_KITCHEN}}
        with self.assertRaises(ValueError) as cm:
            kitchen_name = 'bob'
            self.dk_client.compare_overrides(kitchen_name)
        self.assertEqual(
            f'No kitchen with the name: {kitchen_name} was found in the available kitchens',
            cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_compare_overrides_when__kitchen_not_set_raises_error(self, _):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError):
            dk_client.compare_overrides()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchens_info')
    def test_compare_overrides_when_kitchen_not_found_raises_error(self, mock_get_kitchens_info):
        mock_get_kitchens_info.return_value = {}
        with self.assertRaises(ValueError) as cm:
            self.dk_client.compare_overrides()
        self.assertEqual(
            f'No kitchen with the name: {DUMMY_KITCHEN} was found in the available kitchens',
            cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchens_info')
    def test_compare_overrides(self, mock_get_kitchens_info):
        kitchen_overrides = {'one': 1}
        other_kitchen_overrides = {'two': 2}
        other_kitchen_name = 'bob'
        mock_get_kitchens_info.return_value = {
            DUMMY_KITCHEN: {
                'name': DUMMY_KITCHEN,
                RECIPE_OVERRIDES: kitchen_overrides
            },
            other_kitchen_name: {
                'name': other_kitchen_name,
                RECIPE_OVERRIDES: other_kitchen_overrides
            }
        }
        self.assertEqual(
            DictionaryComparator(kitchen_overrides, other_kitchen_overrides),
            self.dk_client.compare_overrides(other_kitchen_name)
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchens_info')
    def test_compare_overrides_when_other_is_not_specified_then_compared_to_parent(
        self, mock_get_kitchens_info
    ):
        kitchen_overrides = {'one': 1}
        other_kitchen_overrides = {'two': 2}
        other_kitchen_name = 'other'
        mock_get_kitchens_info.return_value = {
            DUMMY_KITCHEN: {
                'name': DUMMY_KITCHEN,
                PARENT_KITCHEN: other_kitchen_name,
                RECIPE_OVERRIDES: kitchen_overrides
            },
            other_kitchen_name: {
                'name': other_kitchen_name,
                RECIPE_OVERRIDES: other_kitchen_overrides
            }
        }
        self.assertEqual(
            DictionaryComparator(kitchen_overrides, other_kitchen_overrides),
            self.dk_client.compare_overrides()
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchen_info')
    def test_get_kitchen_staff(self, mock_get_kitchen_info):
        kitchen_staff = ["ehill+im@datakitchen.io"]
        mock_get_kitchen_info.return_value = {KITCHEN_STAFF: kitchen_staff}
        self.assertEqual(kitchen_staff, self.dk_client.get_kitchen_staff())
        mock_get_kitchen_info.assert_called_once_with()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._update_kitchen')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchen_info')
    def test_update_kitchen_staff(self, mock_get_kitchen_info, mock_update_kitchen_info):
        kitchen_info_with_original_kitchen_staff = {
            "name": DUMMY_KITCHEN,
            KITCHEN_STAFF: [DUMMY_USERNAME]
        }
        new_staff = [DUMMY_USERNAME, "newguy+im@datakitchen.io"]
        kitchen_info_with_new_staff = kitchen_info_with_original_kitchen_staff.copy()
        kitchen_info_with_new_staff[KITCHEN_STAFF] = new_staff
        mock_get_kitchen_info.return_value = kitchen_info_with_original_kitchen_staff
        self.dk_client.update_kitchen_staff(new_staff)
        mock_get_kitchen_info.assert_called_once_with()
        mock_update_kitchen_info.assert_called_once_with(kitchen_info_with_new_staff)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_update_kitchen_staff_when_current_user_is_removed_then_value_error_is_raised(self, _):
        with self.assertRaises(ValueError) as cm:
            self.dk_client.update_kitchen_staff(["some@email.com"])
        self.assertEqual(
            f'Current user: {DUMMY_USERNAME} can not be removed from kitchen staff',
            cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._update_kitchen')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchen_info')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_add_kitchen_staff(self, _, mock_get_kitchen_info, mock_update_kitchen_info):
        kitchen_info_with_original_kitchen_staff = {
            "name": DUMMY_KITCHEN,
            KITCHEN_STAFF: [DUMMY_USERNAME]
        }
        new_staff = [DUMMY_USERNAME, "newguy+im@datakitchen.io"]
        kitchen_info_with_new_staff = kitchen_info_with_original_kitchen_staff.copy()
        kitchen_info_with_new_staff[KITCHEN_STAFF] = new_staff
        mock_get_kitchen_info.return_value = kitchen_info_with_original_kitchen_staff
        self.dk_client.add_kitchen_staff(new_staff)
        mock_get_kitchen_info.assert_has_calls([call(), call()])
        mock_update_kitchen_info.assert_called_once_with(kitchen_info_with_new_staff)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient')
    def test_create_using_default_context(self, mock_client):
        with patch('builtins.open', mock_open(read_data=json.dumps(JSON_PROFILE))) as m:
            create_using_context(
                kitchen=DUMMY_KITCHEN, recipe=DUMMY_RECIPE, variation=DUMMY_VARIATION
            )

        user_home_path = os.path.expanduser('~')
        m.assert_called_once_with(os.path.join(user_home_path, '.dk/default/config.json'))
        mock_client.assert_called_once_with(
            base_url=f'{DUMMY_URL}:{DUMMY_PORT}',
            kitchen=DUMMY_KITCHEN,
            password=DUMMY_PASSWORD,
            recipe=DUMMY_RECIPE,
            username=DUMMY_USERNAME,
            variation=DUMMY_VARIATION
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient')
    def test_create_using_context(self, mock_client):
        with patch('builtins.open', mock_open(read_data=json.dumps(JSON_PROFILE))) as m:
            context = 'test'
            create_using_context(
                context, kitchen=DUMMY_KITCHEN, recipe=DUMMY_RECIPE, variation=DUMMY_VARIATION
            )
        user_home_path = os.path.expanduser('~')
        m.assert_called_once_with(os.path.join(user_home_path, '.dk', context, 'config.json'))
        mock_client.assert_called_once_with(
            base_url=f'{DUMMY_URL}:{DUMMY_PORT}',
            kitchen=DUMMY_KITCHEN,
            password=DUMMY_PASSWORD,
            recipe=DUMMY_RECIPE,
            username=DUMMY_USERNAME,
            variation=DUMMY_VARIATION
        )

    def test_get_override_names_that_do_not_exist_when_none_overrides_given_then_raises_valueerror(
        self
    ):
        with self.assertRaises(ValueError) as cm:
            self.dk_client.get_override_names_that_do_not_exist(None)
        self.assertEqual('At least one override must be specified', cm.exception.args[0])

    def test_get_override_names_that_do_not_exist_when_empty_overrides_given_then_raises_valueerror(
        self
    ):
        with self.assertRaises(ValueError) as cm:
            self.dk_client.get_override_names_that_do_not_exist(set())
        self.assertEqual('At least one override must be specified', cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_overrides')
    def test_get_override_names_that_do_not_exist_when_some_do_not_exist(self, mock_get_overrides):
        existing_name = 'old_guy'
        new_name = 'new_guy'
        mock_get_overrides.return_value = {existing_name: 'bob'}
        self.assertEqual({new_name},
                         self.dk_client.get_override_names_that_do_not_exist({
                             existing_name, new_name
                         }))
        mock_get_overrides.assert_called_once()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_overrides')
    def test_get_override_names_that_do_not_exist_when_all_exist(self, mock_get_overrides):
        overrides = {'one': 1, 'two': 2}
        mock_get_overrides.return_value = overrides
        self.assertEqual(
            set(), self.dk_client.get_override_names_that_do_not_exist(overrides.keys())
        )
        mock_get_overrides.assert_called_once()

    def test_get_override_names_that_exist_when_none_overrides_given_then_raises_valueerror(self):
        with self.assertRaises(ValueError) as cm:
            self.dk_client.get_override_names_that_exist(None)
        self.assertEqual('At least one override must be specified', cm.exception.args[0])

    def test_get_override_names_that_exist_when_empty_overrides_given_then_raises_valueerror(self):
        with self.assertRaises(ValueError) as cm:
            self.dk_client.get_override_names_that_exist(set())
        self.assertEqual('At least one override must be specified', cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_overrides')
    def test_get_override_names_that_exist_when_some_do_not_exist(self, mock_get_overrides):
        existing_name = 'old_guy'
        new_name = 'new_guy'
        mock_get_overrides.return_value = {existing_name: 'bob'}
        self.assertEqual({existing_name},
                         self.dk_client.get_override_names_that_exist({existing_name, new_name}))
        mock_get_overrides.assert_called_once()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_overrides')
    def test_get_override_names_that_exist_when_all_exist(self, mock_get_overrides):
        overrides = {'one': 1, 'two': 2}
        mock_get_overrides.return_value = overrides
        self.assertEqual(
            overrides.keys(), self.dk_client.get_override_names_that_exist(overrides.keys())
        )
        mock_get_overrides.assert_called_once()

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_recipes_when_kitchen_is_not_set_then_value_error_is_raised(self, _):
        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        with self.assertRaises(ValueError) as cm:
            dk_client.get_recipes()
        self.assertEqual('Undefined attributes: kitchen', cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchens_info')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_recipes_when_kitchen_is_not_available_then_value_error_is_raised(
        self, _, mock_get_kitchens_info
    ):
        mock_get_kitchens_info.return_value = {DUMMY_KITCHEN: {'kitchen-staff': []}}
        with self.assertRaises(ValueError) as cm:
            self.dk_client.get_recipes()
        self.assertEqual(
            f'{DUMMY_KITCHEN} is not available to {DUMMY_USERNAME}', cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._get_kitchens_info')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_recipes(self, _, mock_get, mock_kitchens_info):
        mock_kitchens_info.return_value = {DUMMY_KITCHEN: {'kitchen-staff': [DUMMY_USERNAME]}}
        mock_get.return_value = MockResponse(json={'recipes': RECIPES})
        self.assertEqual(RECIPES, self.dk_client.get_recipes())
        mock_get.assert_called_once_with(GET_RECIPES_URL, headers=None, json={})

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_ensure_attributes_when_kitchen_not_set_raises_value_error(self, _):
        self.dk_client.kitchen = None
        self.dk_client.recipe = DUMMY_RECIPE
        self.dk_client.variation = DUMMY_VARIATION
        with self.assertRaises(ValueError) as cm:
            self.dk_client._ensure_attributes(KITCHEN)
        self.assertEqual('Undefined attributes: kitchen', cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_ensure_attributes_when_recipe_not_set_raises_value_error(self, _):
        self.dk_client.kitchen = None
        with self.assertRaises(ValueError) as cm:
            self.dk_client._ensure_attributes(RECIPE)
        self.assertEqual('Undefined attributes: kitchen,recipe', cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_ensure_attributes_when_variation_not_set_raises_value_error(self, _):
        self.dk_client.kitchen
        with self.assertRaises(ValueError) as cm:
            self.dk_client._ensure_attributes(VARIATION)
        self.assertEqual('Undefined attributes: recipe,variation', cm.exception.args[0])

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipes')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_ensure_attributes_when_recipe_invalid(self, _, mock_recipes):
        self.dk_client.recipe = "bad_recipe"
        mock_recipes.return_value = RECIPES
        with self.assertRaises(ValueError) as cm:
            self.dk_client._ensure_attributes(KITCHEN, RECIPE)
        mock_recipes.assert_called_once()
        self.assertEqual(
            f'bad_recipe is not one of the available recipes: {DUMMY_RECIPE}', cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipes')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_ensure_attributes_when_variation_invalid(self, _, mock_recipes):
        self.dk_client.recipe = DUMMY_RECIPE
        self.dk_client.variation = "bad_variation"
        mock_recipes.return_value = RECIPES
        with self.assertRaises(ValueError) as cm:
            self.dk_client._ensure_attributes(KITCHEN, RECIPE, VARIATION)
        mock_recipes.assert_called_once()
        self.assertEqual(
            f'bad_variation is not one of the available variations: {DUMMY_VARIATION}',
            cm.exception.args[0]
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_status(self, _, mock_get):
        response_json = {
            'customer': 'DummyCustomer',
            'kitchenname': 'DummyKitchen',
            'orders': [{
                'hid': 'a8f9ac78-e0ed-11ea-b3f4-56a20effdf97',
                'input_settings': {},
                'order-status': 'COMPLETED_ORDER',
                'recipe': 'Test_Recipe',
                'schedule': 'now',
                'variation': 'variation1'
            }, {
                'hid': '3942feda-e0ec-11ea-a00e-56a20effdf97',
                'input_settings': {},
                'order-status': 'COMPLETED_ORDER',
                'recipe': 'Test_Recipe',
                'schedule': 'now',
                'variation': 'variation1'
            }],
            'repo': 'dc',
            'servings': {
                '3942feda-e0ec-11ea-a00e-56a20effdf97': {
                    'servings': [{
                        'hid': '3f57a7d0-e0ec-11ea-a65f-5edd64ee22f9',
                        'order_id': '3942feda-e0ec-11ea-a00e-56a20effdf97',
                        'orderrun_status': 'OrderRun Completed',
                        'status': 'COMPLETED_SERVING',
                        'timings': {
                            'duration': 22676,
                            'end-time': 1597711609459,
                            'start-time': 1597711586783
                        },
                        'variation_name': 'variation1'
                    }],
                    'total': 1
                },
                'a8f9ac78-e0ed-11ea-b3f4-56a20effdf97': {
                    'servings': [{
                        'hid': '66152846-e0ee-11ea-8280-12128c919b99',
                        'order_id': 'a8f9ac78-e0ed-11ea-b3f4-56a20effdf97',
                        'orderrun_status': 'OrderRun Completed',
                        'status': 'COMPLETED_SERVING',
                        'timings': {
                            'duration': 22261,
                            'end-time': 1597712533033,
                            'start-time': 1597712510772
                        },
                        'variation_name': 'variation1'
                    }],
                    'total': 1
                }
            },
            'total-orders': 2
        }

        expected_order_runs = []
        for order in response_json['servings'].values():
            expected_order_runs.extend(order['servings'])

        def sort_start_time(value):
            return value['timings']['start-time']

        expected_order_runs = sorted(expected_order_runs, key=sort_start_time, reverse=True)

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        mock_get.return_value = MockResponse(json=response_json)
        observed_order_runs = dk_client.get_order_status(
            time_period_hours=24,
            order_id_regex='*',
            order_status='COMPLETED_SERVING',
            order_run_status='OrderRun Completed',
            order_run_count=2,
        )
        self.assertEqual(observed_order_runs, expected_order_runs)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def test_get_order_status_empty(self, _, mock_get):
        response_json = {'servings': {}}

        dk_client = DataKitchenClient(DUMMY_USERNAME, DUMMY_PASSWORD, base_url=DUMMY_URL)
        dk_client.kitchen = DUMMY_KITCHEN
        dk_client.recipe = DUMMY_RECIPE
        dk_client.variation = DUMMY_VARIATION
        mock_get.return_value = MockResponse(json=response_json)
        observed_order_runs = dk_client.get_order_status()
        self.assertEqual(observed_order_runs, [])
