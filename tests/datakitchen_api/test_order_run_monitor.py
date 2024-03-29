from unittest import TestCase
from unittest.mock import patch

from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient
from dkutils.datakitchen_api.order_run_monitor import (
    OrderRunMonitor,
    get_customer_code,
    get_ingredient_owner_order_run_id,
    get_order_run_url,
)
from .test_datakitchen_client import (
    DUMMY_USERNAME,
    DUMMY_PASSWORD,
    DUMMY_URL,
    DUMMY_KITCHEN,
    MockResponse,
)

EVENTS_API_KEY = 'events_api_key'
ORDER_RUN_ID = '053208b4-06ad-11ed-8648-12d0c7010e70'
PIPELINE_NAME = 'kitchen.recipe.variation'
EXPECTED_CONDITIONAL_NODES = ['Condition']
EXPECTED_NODES_TO_IGNORE = ['Order_Run_Monitor'] + EXPECTED_CONDITIONAL_NODES
EXPECTED_SUCCESSFUL_NODES = [
    'Action_Node_Test', 'Condition_True', 'DataMapper_Node_Test', 'Node_After_Sleep', 'Quick_Node',
    'Sleep'
]
EXPECTED_FAILED_NODES = ['Fail_Node']

ORDER_RUN_DETAILS = {
    'conditions': {
        'condition_1_false': {
            'node': 'Condition'
        },
        'condition_1_true': {
            'node': 'Condition'
        }
    },
    'summary': {
        'nodes': {
            'Action_Node_Test': {
                'status': 'DKNodeStatus_completed_production',
                'start_time': 1660678738681,
                'timing': 10000,
                'tests': {},
                'actions': {
                    'source': {
                        'tests': {
                            'Action_Node_Test': {
                                'applies-to-keys': None,
                                'metric': 'condition',
                                'results': 'True '
                                           'equal-to '
                                           'condition=True',
                                'status': 'Passed',
                                'value': True
                            }
                        }
                    }
                }
            },
            'Condition': {
                'status': 'DKNodeStatus_completed_production',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {}
            },
            'Condition_False': {
                'status': 'DKNodeStatus_Skipped',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {}
            },
            'Condition_True': {
                'status': 'DKNodeStatus_completed_production',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {}
            },
            'DataMapper_Node_Test': {
                'status': 'DKNodeStatus_completed_production',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {}
            },
            'Fail_Node': {
                'status': 'DKNodeStatus_production_error',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {
                    'Fail': {
                        'applies-to-keys': [],
                        'metric': 'condition == False',
                        'results': 'True condition == False',
                        'status': 'Failed',
                        'value': True
                    }
                },
            },
            'Node_After_Fail': {
                'status': 'DKNodeStatus_ready_for_production',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {}
            },
            'Node_After_Sleep': {
                'status': 'DKNodeStatus_completed_production',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {}
            },
            'Order_Run_Monitor': {
                'status': 'DKNodeStatus_completed_production',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {}
            },
            'Quick_Node': {
                'status': 'DKNodeStatus_completed_production',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {}
            },
            'Sleep': {
                'status': 'DKNodeStatus_completed_production',
                'start_time': 1660678738681,
                'timing': None,
                'tests': {},
                'data_sinks': {
                    's3_sink': {
                        'tests': {
                            'S3_Sink_Test': {
                                'applies-to-keys': None,
                                'metric': 'condition',
                                'results': 'True '
                                           'condition',
                                'status': 'Passed',
                                'value': True
                            }
                        }
                    }
                },
            }
        }
    }
}

USER_INFO = {
    'customer_git_name': 'im',
    'customer_git_org': 'DKImplementation',
    'customer_name': 'Implementation',
    'email': 'implementation+im@datakitchen.io',
    'email_verified': False,
    'family_name': 'User',
    'given_name': 'Implementation',
    'name': 'implementation+im@datakitchen.io',
    'nickname': 'implementation+im@datakitchen.io',
    'role': 'ADMIN',
    'support_email': 'admin@datakitchen.io',
    'updated_at': '2022-10-05T15:49:41.926Z',
    'user_metadata': {
        'customer': 'Implementation',
        'name': 'Implementation User'
    },
    'wiki_url': ''
}

ORDER_STATUS = {
    'customer': 'DKImplementation',
    'kitchenname': 'test_var_db9f45ce5f10d26a9f2d9cbfecce4db7',
    'orders': [{
        'hid': '2be0e314-4581-11ed-96f0-5ad89aed543c',
        'input_settings': {
            'customer_git_name': 'im',
            'customer_git_org': 'DKImplementation',
            'customer_name': 'Implementation',
            'email': 'ddicara+im@datakitchen.io',
            'email_verified': True,
            'ingredient_owner_order_run': '273def96-4581-11ed-8565-ea3e88365b9c',
            'login': 'ddicara+im@datakitchen.io',
            'parameters': {},
            'role': 'ADMIN',
            'user_id': ''
        },
        'order_status': 'ACTIVE_ORDER',
        'recipe': 'Utility_Monitor_DataKitchen_Events',
        'schedule': None,
        'servings': [],
        'timezone': 'UTC',
        'total_servings': 1,
        'variation': 'Test_Ingredient'
    }],
    'repo': 'im',
    'total': 1
}


class TestOrderRunMonitor(TestCase):

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def setUp(self, _):
        self.dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, kitchen=DUMMY_KITCHEN, base_url=DUMMY_URL
        )

    @patch('dkutils.datakitchen_api.order_run_monitor.ApiClient')
    @patch('dkutils.datakitchen_api.order_run_monitor.get_ingredient_owner_order_run_id')
    @patch('dkutils.datakitchen_api.order_run_monitor.get_customer_code')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_order_run_details')
    def test_nodes_to_ignore(
        self, mock_get_order_run_details, mock_get_customer_code,
        mock_get_ingredient_owner_order_run_id, _
    ):
        mock_get_order_run_details.return_value = ORDER_RUN_DETAILS
        mock_get_customer_code.return_value = 'im'
        mock_get_ingredient_owner_order_run_id.return_value = None
        self.order_run_monitor = OrderRunMonitor(
            self.dk_client, EVENTS_API_KEY, ORDER_RUN_ID, PIPELINE_NAME
        )
        self.assertListEqual(self.order_run_monitor._nodes_to_ignore, EXPECTED_NODES_TO_IGNORE)

    @patch('dkutils.datakitchen_api.order_run_monitor.ApiClient')
    @patch('dkutils.datakitchen_api.order_run_monitor.get_ingredient_owner_order_run_id')
    @patch('dkutils.datakitchen_api.order_run_monitor.get_customer_code')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_order_run_details')
    def test_get_conditional_nodes(
        self, mock_get_order_run_details, mock_get_customer_code,
        mock_get_ingredient_owner_order_run_id, _
    ):
        mock_get_order_run_details.side_effect = [ORDER_RUN_DETAILS, ORDER_RUN_DETAILS]
        mock_get_customer_code.return_value = 'im'
        mock_get_ingredient_owner_order_run_id.return_value = None
        order_run_monitor = OrderRunMonitor(
            self.dk_client, EVENTS_API_KEY, ORDER_RUN_ID, PIPELINE_NAME
        )
        conditional_nodes = order_run_monitor.get_conditional_nodes()
        self.assertListEqual(conditional_nodes, EXPECTED_CONDITIONAL_NODES)

    @patch('dkutils.datakitchen_api.order_run_monitor.ApiClient')
    @patch('dkutils.datakitchen_api.order_run_monitor.get_ingredient_owner_order_run_id')
    @patch('dkutils.datakitchen_api.order_run_monitor.get_customer_code')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_order_run_details')
    def test_monitor(
        self, mock_get_order_run_details, mock_get_customer_code,
        mock_get_ingredient_owner_order_run_id, _
    ):
        mock_get_order_run_details.side_effect = [ORDER_RUN_DETAILS, ORDER_RUN_DETAILS]
        mock_get_customer_code.return_value = 'im'
        mock_get_ingredient_owner_order_run_id.return_value = None
        order_run_monitor = OrderRunMonitor(
            self.dk_client, EVENTS_API_KEY, ORDER_RUN_ID, PIPELINE_NAME
        )
        result = order_run_monitor.monitor()
        self.assertListEqual(result[0], EXPECTED_SUCCESSFUL_NODES)
        self.assertListEqual(result[1], EXPECTED_FAILED_NODES)

    @patch('dkutils.datakitchen_api.order_run_monitor.ApiClient')
    @patch('dkutils.datakitchen_api.order_run_monitor.get_ingredient_owner_order_run_id')
    @patch('dkutils.datakitchen_api.order_run_monitor.get_customer_code')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_order_run_details')
    def test_monitor_ingredient(
        self, mock_get_order_run_details, mock_get_customer_code,
        mock_get_ingredient_owner_order_run_id, _
    ):
        mock_get_order_run_details.side_effect = [ORDER_RUN_DETAILS, ORDER_RUN_DETAILS]
        mock_get_customer_code.return_value = 'im'
        mock_get_ingredient_owner_order_run_id.return_value = ORDER_RUN_ID
        order_run_monitor = OrderRunMonitor(
            self.dk_client, EVENTS_API_KEY, ORDER_RUN_ID, PIPELINE_NAME
        )
        result = order_run_monitor.monitor()
        self.assertListEqual(result[0], [])
        self.assertListEqual(result[1], [])

    def test_get_order_run_url(self):
        order_run_url = get_order_run_url(self.dk_client, 'im', 'order_run_id')
        expected_order_run_url = 'https://dummy/url/#/orders/im/dummy_kitchen/runs/order_run_id'
        self.assertEqual(order_run_url, expected_order_run_url)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_get_customer_code(self, mock_request):
        mock_request.return_value = MockResponse(json=USER_INFO)
        observed_customer_code = get_customer_code(self.dk_client)
        expected_customer_code = 'im'
        self.assertEqual(observed_customer_code, expected_customer_code)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._api_request')
    def test_get_ingredient_owner_order_run_id(self, mock_request):
        mock_request.return_value = MockResponse(json=ORDER_STATUS)
        observed_order_run_id = get_ingredient_owner_order_run_id(self.dk_client)
        expected_order_run_id = ORDER_STATUS['orders'][0]['input_settings'][
            'ingredient_owner_order_run']
        self.assertEqual(observed_order_run_id, expected_order_run_id)
