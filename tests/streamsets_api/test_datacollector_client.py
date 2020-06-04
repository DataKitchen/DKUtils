from unittest import TestCase
from unittest.mock import patch

from dkutils.streamsets_api.datacollector_client import DataCollectorClient, PipelineStatus
from tests.datakitchen_api.test_datakitchen_client import MockResponse

PORT = 80
HOST = 'localhost'
USER = 'someone'
PASSWORD = 'secret'
AUTH = (USER, PASSWORD)
BASE_URL = f'http://{HOST}:{PORT}/rest/v1/'
PIPELINE_ID = "mcctoscccopy6d3074d9-9d77-4d47-81a8-61b840511a67"
PIPELINE_STATUS = {
    "pipelineId": PIPELINE_ID,
    "rev": "0",
    "user": "admin",
    "status": "FINISHED",
    "message": None,
    "timeStamp": 1591191043662,
    "attributes": {
        "IS_REMOTE_PIPELINE": False,
        "RUNTIME_PARAMETERS": None,
        "INTERCEPTOR_CONFIGS": []
    },
    "executionMode": "STANDALONE",
    "metrics": "",
    "retryAttempt": 0,
    "nextRetryTimeStamp": 0,
    "name": PIPELINE_ID
}


class TestDataCollectorClient(TestCase):

    def test_constructor(self):
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        self.assertEqual(AUTH, client._auth)
        self.assertEqual(BASE_URL, client._base_url)

    def test_get_pipeline_status_raises_valueerror_when_pipeline_id_is_missing(self):
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        with self.assertRaises(ValueError):
            client.get_pipeline_status(None)

    @patch('dkutils.streamsets_api.datacollector_client.requests.get')
    def test_get_pipeline_full_status(self, mock_get):
        mock_get.return_value = MockResponse(json=PIPELINE_STATUS)
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        status = client.get_pipeline_full_status(PIPELINE_ID)
        mock_get.assert_called_once_with(f'{BASE_URL}pipeline/{PIPELINE_ID}/status?rev=0', auth=AUTH, json={})
        self.assertEqual(PIPELINE_STATUS, status)

    @patch('dkutils.streamsets_api.datacollector_client.requests.get')
    def test_get_pipeline_status(self, mock_get):
        mock_get.return_value = MockResponse(json=PIPELINE_STATUS)
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        status = client.get_pipeline_status(PIPELINE_ID)
        mock_get.assert_called_once_with(f'{BASE_URL}pipeline/{PIPELINE_ID}/status?rev=0', auth=AUTH, json={})
        self.assertEqual(PipelineStatus.FINISHED, status)

    def test_start_pipeline_raises_valueerror_when_pipeline_id_is_missing(self):
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        with self.assertRaises(ValueError):
            client.start_pipeline(None)

    @patch('dkutils.streamsets_api.datacollector_client.requests.post')
    def test_start_pipeline_without_runtime_parameters(self, mock_post):
        mock_post.return_value = MockResponse(json=PIPELINE_STATUS)
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        status = client.start_pipeline(PIPELINE_ID)
        mock_post.assert_called_once_with(f'{BASE_URL}pipeline/{PIPELINE_ID}/start?rev=0', auth=AUTH, json={})
        self.assertEqual(PIPELINE_STATUS, status)

    @patch('dkutils.streamsets_api.datacollector_client.requests.post')
    def test_start_pipeline_with_runtime_parameters(self, mock_post):
        mock_post.return_value = MockResponse(json=PIPELINE_STATUS)
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        runtime_parameters = {"table_name": "table_one"}
        status = client.start_pipeline(PIPELINE_ID, **runtime_parameters)
        mock_post.assert_called_once_with(f'{BASE_URL}pipeline/{PIPELINE_ID}/start?rev=0', auth=AUTH,
                                          json=runtime_parameters)
        self.assertEqual(PIPELINE_STATUS, status)

    def test_reset_pipeline_raises_valueerror_when_pipeline_id_is_missing(self):
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        with self.assertRaises(ValueError):
            client.reset_pipeline(None)

    @patch('dkutils.streamsets_api.datacollector_client.requests.post')
    def test_reset_pipeline(self, mock_post):
        client = DataCollectorClient(HOST, PORT, USER, PASSWORD)
        client.reset_pipeline(PIPELINE_ID)
        mock_post.assert_called_once_with(f'{BASE_URL}pipeline/{PIPELINE_ID}/resetOffset?rev=0', auth=AUTH,
                                          json={})
