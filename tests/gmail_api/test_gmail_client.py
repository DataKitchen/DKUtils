import base64
import pickle
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dkutils.gmail_api.gmail_client import create_base64_encoded_token, GmailClientException, \
    get_object_from_environment, GMailClient

PARENT = Path(__file__).parent
RESOURCES = PARENT / "resources"


class TestGmailClient(TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_create_base64_encoded_token_when_credentials_path_does_not_exist_then_raises_gmailclientexception(self):
        with self.assertRaises(GmailClientException) as cm:
            create_base64_encoded_token(PARENT / "bogus", PARENT / "bogus")
        self.assertEqual("Credentials file must exist", cm.exception.args[0])

    @patch('dkutils.gmail_api.gmail_client.pickle')
    @patch('dkutils.gmail_api.gmail_client.InstalledAppFlow')
    def test_create_base64_encoded_token(self, mock_installed_app_flow, mock_pickle):
        base64_token_file = Path(self.test_dir.name) / 'token.b64'
        credentials_file = RESOURCES / "credentials.json"
        pickled_bytes = "123".encode()
        mock_pickle.dumps.return_value = pickled_bytes

        create_base64_encoded_token(credentials_file, base64_token_file)

        mock_installed_app_flow.from_client_secrets_file.assert_called_once_with(credentials_file, [
            'https://www.googleapis.com/auth/gmail.readonly'])
        mock_installed_app_flow.from_client_secrets_file.return_value.run_local_server.assert_called_once_with(port=0)
        mock_pickle.dumps.assert_called_once_with(
            mock_installed_app_flow.from_client_secrets_file.return_value.run_local_server.return_value)
        self.assertTrue(base64_token_file.exists(), f'{base64_token_file.name} should have been created')
        with base64_token_file.open("rb") as input:
            data = input.read()
        self.assertEqual(pickled_bytes, base64.b64decode(data))

    @patch('os.getenv')
    def test_get_token_from_environment(self, mock_getenv):
        thing = {}
        pickled_thing = pickle.dumps(thing)
        mock_getenv.return_value = base64.b64encode(pickled_thing).decode()
        variable_name = "GMAIL_CREDS"

        self.assertEqual(thing, get_object_from_environment(variable_name))

        mock_getenv.assert_called_once_with(variable_name)

    @patch('dkutils.gmail_api.gmail_client.build')
    def test_constructor(self, mock_build):
        creds = {}

        GMailClient(creds)

        mock_build.assert_called_with('gmail', 'v1', credentials=creds)
