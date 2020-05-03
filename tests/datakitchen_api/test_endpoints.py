from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError

from dkutils.datakitchen_api.endpoints import (
    get_headers,
    create_order,
    get_order_runs,
    get_order_run_details,
)

from .test_datakitchen_client import (
    DUMMY_AUTH_TOKEN,
    DUMMY_HEADERS,
    DUMMY_KITCHEN,
    DUMMY_ORDER_RUN_ID,
)


class TestEndpoints(TestCase):

    @patch('dkutils.datakitchen_api.endpoints.requests.post')
    def test_get_headers(self, mock_post):
        mock_post.return_value.text = DUMMY_AUTH_TOKEN
        headers = get_headers('Foo', 'Bar')
        self.assertEqual(headers, DUMMY_HEADERS)

    def test_get_headers_exception(self):
        with self.assertRaises(HTTPError):
            get_headers('Foo', 'Bar')

    @patch('dkutils.datakitchen_api.endpoints.requests.put')
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

    @patch('dkutils.datakitchen_api.endpoints.requests.get')
    def test_get_order_runs(self, mock_get):
        order_id = '71d8a966-38e0-11ea-8cf9-a6bbea194887'
        kitchen = 'Foo'
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
        mock_get.return_value.json = lambda: response_json
        order_runs = get_order_runs(DUMMY_HEADERS, kitchen, order_id)
        self.assertEqual(order_runs, response_json['servings'])

    @patch('dkutils.datakitchen_api.endpoints.requests.get')
    def test_get_order_runs_raise_exception(self, mock_get):
        order_id = '71d8a966-38e0-11ea-8cf9-a6bbea194887'
        kitchen = 'Foo'
        mock_get.return_value.raise_for_status.side_effect = HTTPError('Failed API Call')
        self.assertIsNone(get_order_runs(DUMMY_HEADERS, kitchen, order_id))

    @patch('dkutils.datakitchen_api.endpoints.requests.post')
    def test_get_order_run_details(self, mock_post):
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
        mock_post.return_value.json = lambda: response_json
        order_run_details = get_order_run_details(DUMMY_HEADERS, DUMMY_KITCHEN, DUMMY_ORDER_RUN_ID)
        self.assertEqual(order_run_details, response_json['servings'][0])

    @patch('dkutils.datakitchen_api.endpoints.requests.post')
    def test_get_order_run_details_fail(self, mock_post):
        mock_post.return_value.raise_for_status.side_effect = HTTPError('Failed API Call')
        with self.assertRaises(HTTPError):
            get_order_run_details(DUMMY_HEADERS, DUMMY_KITCHEN, DUMMY_ORDER_RUN_ID)
