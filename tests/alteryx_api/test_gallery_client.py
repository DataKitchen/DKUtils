import copy
from unittest import TestCase
from unittest.mock import patch

from dkutils.alteryx_api.gallery_client import GalleryException, GalleryClient, JobInfo, Workflow, JobInfoMessage, \
    MetaInfo

META_INFO_DICT = {
    'name': 'FL-Asset-Model',
    'description': 'Fund Liquidity Asset Model',
    'author': '',
    'copyright': '',
    'url': '',
    'urlText': '',
    'outputMessage': '',
    'noOutputFilesMessage': ''
}

JOB_INFO_MESSAGE_DICT = {"status": 1, "text": "some text", "toolId": 325}

API_LOCATION = "http://someserver.com/gallery"
API_KEY = "SOME KEY"
API_SECRET = "SOME SECRET"
MOCK_AUTHENTICATION = "auth"
APP_ID = '123'
JOB_INFO_MESSAGE_DICT = {"status": 1, "text": "some text", "toolId": 325}
JOB_INFO_DICT = {
    'id': '5fd78ecdf5640000b4006aee',
    'appId': None,
    'createDate': '2020-12-14T16:11:57.7372208Z',
    'status': 'Queued',
    'disposition': 'None',
    'outputs': [],
    'messages': [JOB_INFO_MESSAGE_DICT],
    'priority': 0,
    'workerTag': '',
    'runWithE2': False
}
WORKFLOW_DICT = {
    'id': '5fc63ba8da0c4512187d94e0',
    'subscriptionId': '5fbd6910da0c450a2c4bc941',
    'public': False,
    'runDisabled': False,
    'packageType': 1,
    'uploadDate': '2020-12-01T12:48:40.408Z',
    'fileName': 'FL-Asset-Model.yxmd',
    'metaInfo': META_INFO_DICT,
    'isChained': False,
    'version': 1,
    'runCount': 0,
    'workerTag': '',
    'isE2': False
}
JOB_INFO = JobInfo(**JOB_INFO_DICT)
WORKFLOW = Workflow(**WORKFLOW_DICT)


class GalleryClientTest(TestCase):

    def setUp(self) -> None:
        self.client = GalleryClient(
            api_key=API_KEY, api_location=API_LOCATION, api_secret=API_SECRET
        )

    def test_messages_embedded_as_dict_become_job_info_dataclass(self):
        self.assertEqual(JobInfoMessage(**JOB_INFO_MESSAGE_DICT), JOB_INFO.messages[0])

    def test_meta_info_embedded_as_dict_becomes_metainfo_dataclass(self):
        self.assertEqual(MetaInfo(**META_INFO_DICT), WORKFLOW.metaInfo)

    def test_constructor_when_api_location_is_missing_then_gallery_exception_is_raised(self):
        with self.assertRaises(GalleryException) as cm:
            GalleryClient(api_location=None, api_key=API_KEY, api_secret=API_SECRET)
        self.assertEqual("'api_location' cannot be empty", cm.exception.args[0])

    def test_constructor_when_api_key_is_missing_then_gallery_exception_is_raised(self):
        with self.assertRaises(GalleryException) as cm:
            GalleryClient(api_location=API_LOCATION, api_key=None, api_secret=API_SECRET)
        self.assertEqual("'api_key' cannot be empty", cm.exception.args[0])

    def test_constructor_when_api_secret_is_missing_then_gallery_exception_is_raised(self):
        with self.assertRaises(GalleryException) as cm:
            GalleryClient(api_location=API_LOCATION, api_key=API_KEY, api_secret=None)
        self.assertEqual("'api_secret' cannot be empty", cm.exception.args[0])

    @patch('dkutils.alteryx_api.gallery_client.OAuth1')
    def test_get_authentication(self, mock_authentication):
        self.client._get_authentication()
        mock_authentication.assert_called_once_with(API_KEY, API_SECRET)

    @patch('dkutils.alteryx_api.gallery_client.requests')
    @patch('dkutils.alteryx_api.gallery_client.GalleryClient._get_authentication')
    def test_get(self, mock_get_authentication, mock_requests):
        suffix = "/something/"
        params = {"one": "1"}
        kwargs = {"first": "one"}
        expected_response = {}
        mock_requests.get.return_value.json.return_value = expected_response
        response = self.client._get(suffix, params, **kwargs)
        self.assertEqual(expected_response, response)
        mock_get_authentication.assert_called_once()
        mock_requests.get.assert_called_once_with(
            API_LOCATION + suffix, auth=mock_get_authentication(), params=params, **kwargs
        )
        mock_requests.get.return_value.raise_for_status.assert_called_once()

    @patch('dkutils.alteryx_api.gallery_client.requests')
    @patch('dkutils.alteryx_api.gallery_client.GalleryClient._get_authentication')
    def test_post(self, mock_get_authentication, mock_requests):
        suffix = "/something/"
        params = {"one": "1"}
        kwargs = {"first": "one"}
        expected_response = {}
        mock_requests.post.return_value.json.return_value = expected_response
        response = self.client._post(suffix, params, **kwargs)
        self.assertEqual(expected_response, response)
        mock_get_authentication.assert_called_once()
        mock_requests.post.assert_called_once_with(
            API_LOCATION + suffix, auth=mock_get_authentication(), params=params, **kwargs
        )
        mock_requests.post.return_value.raise_for_status.assert_called_once()

    @patch('dkutils.alteryx_api.gallery_client.GalleryClient._get')
    def test_get_subscription_workflows(self, mock_get):
        mock_get.return_value = [WORKFLOW_DICT]
        self.assertEqual([WORKFLOW], self.client.get_subscription_workflows())
        mock_get.assert_called_once_with("/v1/workflows/subscription/")

    @patch('dkutils.alteryx_api.gallery_client.GalleryClient._get')
    def test_get_all_workflows(self, mock_get):
        mock_get.return_value = [WORKFLOW_DICT]
        self.assertEqual([WORKFLOW], self.client.get_all_workflows())
        mock_get.assert_called_once_with("/admin/v1/workflows/all/")

    @patch('dkutils.alteryx_api.gallery_client.GalleryClient._post')
    def test_execute_workflow(self, mock_post):
        mock_post.return_value = JOB_INFO_DICT
        self.assertEqual(JOB_INFO, self.client.execute_workflow(APP_ID))
        mock_post.assert_called_once_with(f"/v1/workflows/{APP_ID}/jobs/")

    @patch('dkutils.alteryx_api.gallery_client.GalleryClient.execute_workflow')
    @patch('dkutils.alteryx_api.gallery_client.WaitLoop')
    def test_execute_workflow_and_wait_when_timeout_then_galleryexception_raised(
        self, mock_waitloop, mock_execute_workflow
    ):
        mock_waitloop.return_value.__bool__.return_value = False
        with self.assertRaises(GalleryException) as cm:
            self.client.execute_workflow_and_wait(APP_ID)
        self.assertEqual("Timed out after: 3 seconds", cm.exception.args[0])
        mock_execute_workflow.assert_called_once_with(app_id=APP_ID)

    @patch('dkutils.alteryx_api.gallery_client.GalleryClient.execute_workflow')
    @patch('dkutils.alteryx_api.gallery_client.GalleryClient.get_job_status')
    @patch('dkutils.alteryx_api.gallery_client.WaitLoop')
    def test_execute_workflow_and_wait(self, _, mock_get_job_status, mock_execute_workflow):
        mock_execute_workflow.return_value = JOB_INFO
        job_info = copy.copy(JOB_INFO)
        job_info.status = 'Completed'
        mock_get_job_status.return_value = job_info
        self.assertEqual(job_info, self.client.execute_workflow_and_wait(APP_ID))
        mock_execute_workflow.assert_called_once_with(app_id=APP_ID)
        mock_get_job_status.assert_called_once_with(JOB_INFO.id)

    @patch('dkutils.alteryx_api.gallery_client.GalleryClient._get')
    def test_get_job_status(self, mock_get):
        job_id = '123'
        mock_get.return_value = JOB_INFO_DICT
        self.assertEqual(JOB_INFO, self.client.get_job_status(job_id))
        mock_get.assert_called_once_with(f"/v1/jobs/{job_id}/")
