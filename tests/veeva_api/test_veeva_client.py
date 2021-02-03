from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError

from dkutils.veeva_api.veeva_client import VeevaClient

DNS = 'somewhere.com'
USERNAME = 'someone@somewhere.com'
PASSWORD = 'secret'
SYSTEM_NAME = 'somewhere'
SUBSCRIPTION_TYPE = 'source'
SUBSCRIPTION_NAME = 'name'
DEFAULT_VERSION = 'v16.0'
VERSION = 'v17.0'


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


class TestVeevaClient(TestCase):

    @patch('dkutils.veeva_api.veeva_client.requests')
    def setUp(self, mock_requests):
        mock_requests.post.return_value = MockResponse(json={"sessionId": "123"})

        self.client = VeevaClient(dns=DNS, username=USERNAME, password=PASSWORD, system_name=SYSTEM_NAME,
                                  subscription_type=SUBSCRIPTION_TYPE, subscription_name=SUBSCRIPTION_NAME)

    @patch('dkutils.veeva_api.veeva_client.requests')
    def test_constructor_when_post_fails(self, mock_requests):
        base_url = f'https://{DNS}/api/{DEFAULT_VERSION}/'
        mock_requests.post.return_value = MockResponse(raise_error=True)

        with self.assertRaises(HTTPError) as cm:
            VeevaClient(dns=DNS, username=USERNAME, password=PASSWORD, system_name=SYSTEM_NAME,
                        subscription_type=SUBSCRIPTION_TYPE, subscription_name=SUBSCRIPTION_NAME)
        self.assertEqual('Failed API Call', cm.exception.args[0])
        mock_requests.post.assert_called_with(base_url + 'auth', data={'username': USERNAME, 'password': PASSWORD})

    @patch('dkutils.veeva_api.veeva_client.requests')
    def test_constructor_when_cannot_get_authorization(self, mock_requests):
        base_url = f'https://{DNS}/api/{DEFAULT_VERSION}/'
        mock_requests.post.return_value = MockResponse(json={})

        with self.assertRaises(ValueError) as cm:
            VeevaClient(dns=DNS, username=USERNAME, password=PASSWORD, system_name=SYSTEM_NAME,
                        subscription_type=SUBSCRIPTION_TYPE, subscription_name=SUBSCRIPTION_NAME)
        self.assertEqual('Could not get an authorization header', cm.exception.args[0])
        mock_requests.post.assert_called_with(base_url + 'auth', data={'username': USERNAME, 'password': PASSWORD})

    @patch('dkutils.veeva_api.veeva_client.requests')
    def test_constructor(self, mock_requests):
        base_url = f'https://{DNS}/api/{DEFAULT_VERSION}/'
        mock_requests.post.return_value = MockResponse(json={"sessionId": "123"})

        client = VeevaClient(dns=DNS, username=USERNAME, password=PASSWORD, system_name=SYSTEM_NAME,
                             subscription_type=SUBSCRIPTION_TYPE, subscription_name=SUBSCRIPTION_NAME)

        mock_requests.post.assert_called_with(base_url + 'auth', data={'username': USERNAME, 'password': PASSWORD})
        self.assertEqual(base_url, client.base_url)
        self.assertEqual(SYSTEM_NAME, client.system_name)
        self.assertEqual(SUBSCRIPTION_NAME, client.subscription_name)
        self.assertEqual(SUBSCRIPTION_TYPE, client.subscription_type)

    @patch('dkutils.veeva_api.veeva_client.requests')
    def test_run_subscription_process_when_post_fails(self, mock_requests):
        mock_requests.post.return_value = MockResponse(raise_error=True)

        with self.assertRaises(HTTPError) as cm:
            self.client.run_subscription_process()

        self.assertEqual('Failed API Call', cm.exception.args[0])

    @patch('dkutils.veeva_api.veeva_client.requests')
    def test_run_subscription_process_when_post_fails(self, mock_requests):
        job_id = "456"
        mock_requests.post.return_value = MockResponse(json={"job_id": job_id})

        self.assertEqual(job_id, self.client.run_subscription_process())

        base_url = f'https://{DNS}/api/{DEFAULT_VERSION}/'
        mock_requests.post.assert_called_with(
            f'{base_url}systems/{SYSTEM_NAME}/{SUBSCRIPTION_TYPE}_subscriptions/{SUBSCRIPTION_NAME}/job')
