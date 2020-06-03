from unittest import TestCase
from unittest.mock import patch

from dkutils.datakitchen_api.streamsets_datacollector_client import StreamSetsDataCollectorClient, PipelineStatus
from tests.datakitchen_api.test_datakitchen_client import MockResponse

PORT = 80
HOST = 'localhost'
USER = 'someone'
PASSWORD = 'secret'


class TestStreamSetsDataCollectorClient(TestCase):

    def test_constructor(self):
        client = StreamSetsDataCollectorClient(HOST, PORT, USER, PASSWORD)
        self.assertEqual((USER, PASSWORD), client._auth)
        self.assertEqual(f'http://{HOST}:{PORT}/rest/v1/', client._base_url)

    def test_get_pipline_status_raises_valueerror_when_pipeline_id_is_missing(self):
        client = StreamSetsDataCollectorClient(HOST, PORT, USER, PASSWORD)
        with self.assertRaises(ValueError):
            client.get_pipeline_status(None)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_pipeline_full_status(self, mock_get):
        pipeline_id = "mcctoscccopy6d3074d9-9d77-4d47-81a8-61b840511a67"
        response_json = {
            "pipelineId": pipeline_id,
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
            "name": pipeline_id
        }
        mock_get.return_value = MockResponse(json=response_json)
        client = StreamSetsDataCollectorClient(HOST, PORT, USER, PASSWORD)
        status = client.get_pipeline_full_status(pipeline_id)
        self.assertEqual(response_json, status)

    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_pipeline_status(self, mock_get):
        pipeline_id = "mcctoscccopy6d3074d9-9d77-4d47-81a8-61b840511a67"
        response_json = {
            "status": "FINISHED",
        }
        mock_get.return_value = MockResponse(json=response_json)
        client = StreamSetsDataCollectorClient(HOST, PORT, USER, PASSWORD)
        status = client.get_pipeline_status(pipeline_id)
        self.assertEqual(PipelineStatus.FINISHED, status)
