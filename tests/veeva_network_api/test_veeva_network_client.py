from unittest import TestCase
from unittest.mock import patch, call

from requests.exceptions import HTTPError

from dkutils.veeva_network_api.veeva_network_client import VeevaNetworkClient, VeevaSourceSubscriptionClient, \
    VeevaTargetSubscriptionClient, VeevaNetworkException

DNS = 'somewhere.com'
USERNAME = 'someone@somewhere.com'
PASSWORD = 'secret'
SYSTEM_NAME = 'somewhere'
SUBSCRIPTION_TYPE = 'source'
SUBSCRIPTION_NAME = 'name'
DEFAULT_VERSION = 'v16.0'
VERSION = 'v17.0'
BASE_URL = f'https://{DNS}/api/{DEFAULT_VERSION}/'
JOB_RESPONSE_ID = "123"


def get_status_call(client):
    return call(
        f'{BASE_URL}systems/{SYSTEM_NAME}/{client.subscription_type}_subscriptions/'
        f'{SUBSCRIPTION_NAME}/job/{JOB_RESPONSE_ID}',
        headers=client.admin_header
    )


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


class TestVeevaNetworkClient(TestCase):

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_constructor_when_post_fails(self, mock_requests):
        base_url = f'https://{DNS}/api/{DEFAULT_VERSION}/'
        mock_requests.post.return_value = MockResponse(raise_error=True)

        with self.assertRaises(HTTPError) as cm:
            VeevaNetworkClient(
                dns=DNS, username=USERNAME, password=PASSWORD, version=DEFAULT_VERSION
            )
        self.assertEqual('Failed API Call', cm.exception.args[0])
        mock_requests.post.assert_called_with(
            base_url + 'auth', data={
                'username': USERNAME,
                'password': PASSWORD
            }
        )

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_constructor_when_cannot_get_authorization(self, mock_requests):
        base_url = f'https://{DNS}/api/{DEFAULT_VERSION}/'
        mock_requests.post.return_value = MockResponse(json={})

        with self.assertRaises(VeevaNetworkException) as cm:
            VeevaNetworkClient(
                dns=DNS, username=USERNAME, password=PASSWORD, version=DEFAULT_VERSION
            )
        self.assertEqual('Could not get an authorization header', cm.exception.args[0])
        mock_requests.post.assert_called_with(
            base_url + 'auth', data={
                'username': USERNAME,
                'password': PASSWORD
            }
        )

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_constructor(self, mock_requests):
        base_url = f'https://{DNS}/api/{DEFAULT_VERSION}/'
        mock_requests.post.return_value = MockResponse(json={"sessionId": "123"})

        client = VeevaNetworkClient(
            dns=DNS, username=USERNAME, password=PASSWORD, version=DEFAULT_VERSION
        )

        mock_requests.post.assert_called_with(
            base_url + 'auth', data={
                'username': USERNAME,
                'password': PASSWORD
            }
        )
        self.assertEqual(base_url, client.base_url)


class TestVeevaSourceSubscriptionClient(TestCase):

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def setUp(self, mock_requests):
        mock_requests.post.return_value = MockResponse(json={"sessionId": "123"})

        self.client = VeevaSourceSubscriptionClient(
            dns=DNS,
            username=USERNAME,
            password=PASSWORD,
            system_name=SYSTEM_NAME,
            subscription_name=SUBSCRIPTION_NAME
        )

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_run_subscription_process_when_post_fails(self, mock_requests):
        mock_requests.post.return_value = MockResponse(raise_error=True)

        with self.assertRaises(HTTPError) as cm:
            self.client.run_subscription_process()

        self.assertEqual('Failed API Call', cm.exception.args[0])

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_run_subscription_process_when_post_succeeds(self, mock_requests):
        job_id = "456"
        json = {"responseStatus": "SUCCESS", "job_id": job_id}
        mock_requests.post.return_value = MockResponse(json=json)

        self.assertEqual(job_id, self.client.run_subscription_process())

        mock_requests.post.assert_called_with(
            f'{BASE_URL}systems/{SYSTEM_NAME}/{SUBSCRIPTION_TYPE}_subscriptions/{SUBSCRIPTION_NAME}/job',
            headers=self.client.admin_header
        )

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_run_subscription_process_when_job_fails_then_raises_value_error(self, mock_requests):
        json = {
            'responseStatus':
                'FAILURE',
            'responseMessage':
                'Authentication failed for session id: null.; API error message: Authentication failed for session id: null.',
            'errorCodes':
                None,
            'networkExceptionType': {
                'resourceId': 'INVALID_SESSION_ID',
                'parameters': [None]
            },
            'errors': [{
                'type': 'INVALID_SESSION_ID',
                'message': 'Authentication failed for session id: null.'
            }],
            'errorType':
                'GENERAL'
        }
        mock_requests.post.return_value = MockResponse(json=json)

        with self.assertRaises(VeevaNetworkException) as cm:
            self.assertEqual("123", self.client.run_subscription_process())

        self.assertEqual(
            f"The job could not be started. Status: {json['responseStatus']} - {json['responseMessage']}",
            cm.exception.args[0]
        )

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_retrieve_network_process_job_when_get_fails_raises_httperror(self, mock_requests):
        mock_requests.get.return_value = MockResponse(raise_error=True)

        with self.assertRaises(HTTPError) as cm:
            self.client.retrieve_network_process_job(job_resp_id=JOB_RESPONSE_ID)

        self.assertEqual('Failed API Call', cm.exception.args[0])
        mock_requests.get.assert_has_calls([get_status_call(self.client)])

    @patch('dkutils.veeva_network_api.veeva_network_client.time')
    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_retrieve_network_process_job_when_second_get_fails_raises_httperror(
        self, mock_requests, mock_time
    ):
        mock_requests.get.side_effect = [
            MockResponse(json={
                "responseStatus": "SUCCESS",
                "job_status": "RUNNING"
            }),
            MockResponse(raise_error=True)
        ]

        with self.assertRaises(HTTPError) as cm:
            self.client.retrieve_network_process_job(job_resp_id="123")

        self.assertEqual('Failed API Call', cm.exception.args[0])
        mock_time.sleep.assert_called_with(5)

        mock_requests.get.assert_has_calls([
            get_status_call(self.client),
            get_status_call(self.client)
        ])

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_retrieve_network_process_job_when_job_status_can_not_be_retried_then_raises_exception(
        self, mock_requests
    ):
        json = {
            'responseStatus': 'FAILURE',
            'errors': [{
                'type':
                    'UNEXPECTED_ERROR',
                'message':
                    'Subscription and job not matched: job 123 does not belong to subscription 83'
            }],
            'errorType': 'UNEXPECTED_ERROR'
        }
        mock_requests.get.return_value = MockResponse(json=json)

        with self.assertRaises(VeevaNetworkException) as cm:
            self.client.retrieve_network_process_job(job_resp_id="123")

        self.assertEqual(
            f"The job status could not be retrieved. Status: {json['responseStatus']} - {json['errorType']}",
            cm.exception.args[0]
        )

        mock_requests.get.assert_has_calls([get_status_call(self.client)])

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_retrieve_network_process_job_when_job_ends_in_unexpected_status(self, mock_requests):
        mock_requests.get.return_value = MockResponse(
            json={
                "responseStatus": "SUCCESS",
                "job_status": "FAILED"
            }
        )

        with self.assertRaises(VeevaNetworkException) as cm:
            self.client.retrieve_network_process_job(job_resp_id="123")

        self.assertEqual(
            'The job has terminated with an unexpected status: FAILED', cm.exception.args[0]
        )

        mock_requests.get.assert_has_calls([get_status_call(self.client)])

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_retrieve_network_process_job_when_subscription_type_is_source_then_returns_source_info(
        self, mock_requests
    ):
        errorCount = 0
        recordCount = 1
        badRecordCount = 2
        mock_requests.get.return_value = MockResponse(
            json={
                "responseStatus": "SUCCESS",
                "job_status": "COMPLETE",
                "errorCount": errorCount,
                "recordCount": recordCount,
                "badRecordCount": badRecordCount
            }
        )
        expected = {
            'source_subscription_errorcount': str(errorCount),
            'source_subscription_recordcount': str(recordCount),
            'source_subscription_badrecordcount': str(badRecordCount)
        }
        self.assertEqual(expected, self.client.retrieve_network_process_job(job_resp_id="123"))

        mock_requests.get.assert_has_calls([get_status_call(self.client)])


class TestVeevaTargetSubscriptionClient(TestCase):

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def setUp(self, mock_requests):
        mock_requests.post.return_value = MockResponse(
            json={
                "responseStatus": "SUCCESS",
                "sessionId": "123"
            }
        )

        self.client = VeevaTargetSubscriptionClient(
            dns=DNS,
            username=USERNAME,
            password=PASSWORD,
            system_name=SYSTEM_NAME,
            subscription_name=SUBSCRIPTION_NAME
        )

    @patch('dkutils.veeva_network_api.veeva_network_client.requests')
    def test_retrieve_network_process_job_when_subscription_type_is_source_then_returns_source_info(
        self, mock_requests
    ):
        address = "123"
        customkey = "something big"
        hco = "hco thing"
        hcp = "hcp thing"
        license = "ok"
        parenthco = "dad"
        badRecordCount = 2
        json = {
            "responseStatus": "SUCCESS",
            "job_status": "COMPLETE",
            "jobExportCount": {
                "ADDRESS": address,
                "CUSTOMKEY": customkey,
                "HCO": hco,
                "HCP": hcp,
                "LICENSE": license,
                "PARENTHCO": parenthco
            },
            "badRecordCount": badRecordCount
        }
        mock_requests.get.return_value = MockResponse(json=json)
        expected = {
            'target_subscription_ADDRESS_count': address,
            'target_subscription_CUSTOMKEY_count': customkey,
            'target_subscription_HCO_count': str(hco),
            'target_subscription_HCP_count': str(hcp),
            'target_subscription_LICENSE_count': str(license),
            'target_subscription_PARENTHCO_count': parenthco,
            'target_subscription_badrecordcount': str(badRecordCount)
        }

        self.assertEqual(expected, self.client.retrieve_network_process_job(job_resp_id="123"))

        mock_requests.get.assert_has_calls([get_status_call(self.client)])
