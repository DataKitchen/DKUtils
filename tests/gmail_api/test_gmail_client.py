import base64
import pickle
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, call, MagicMock

from dkutils.constants import GMAIL_APPROVAL_STRING
from dkutils.gmail_api.gmail_client import create_base64_encoded_token, GmailClientException, \
    get_object_from_environment, GMailClient, create_message, create_message_with_attachment

PARENT = Path(__file__).parent
RESOURCES = PARENT / "resources"
SAMPLE_TEXT = RESOURCES / "sample.txt"
SAMPLE_IMAGE = RESOURCES / 'sample.gif'
SAMPLE_AUDIO = RESOURCES / 'sample.mp3'
SAMPLE_OTHER = RESOURCES / 'sample.ocdf'
TO = "someone@somewhere.com"
FROM = "person@elsewher.com"
SUBJECT = "Good News"
MSG_TEXT = "This is an important message for you"
MESSAGE = {}
SENT_MESSAGE = {"id": "123"}


class Test(TestCase):

    @patch('dkutils.gmail_api.gmail_client.MIMEText')
    @patch('dkutils.gmail_api.gmail_client.base64')
    def test_create_message(self, mock_base64, mock_mime_text):
        message_as_byte = bytes('test', 'utf-8')
        mock_message = mock_mime_text.return_value
        mock_message.as_bytes.return_value = message_as_byte
        decoded = "decoded"
        mock_base64.urlsafe_b64encode.return_value.decode.return_value = decoded

        msg = create_message(sender=FROM, to=TO, subject=SUBJECT, message_text=MSG_TEXT)

        self.assertEqual({"raw": decoded}, msg)
        calls = [call('to', TO), call('from', FROM), call('subject', SUBJECT)]
        mock_message.__setitem__.assert_has_calls(calls)

    @patch('dkutils.gmail_api.gmail_client.MIMEText')
    @patch('dkutils.gmail_api.gmail_client.base64')
    @patch('dkutils.gmail_api.gmail_client.MIMEMultipart')
    def test_create_message_with_attachment_when_text_file(
        self, mock_mime_multipart, mock_base64, mock_mime_text
    ):
        message_as_byte = bytes('test', 'utf-8')
        mock_message = mock_mime_multipart.return_value
        mock_message.as_bytes.return_value = message_as_byte
        decoded = "decoded"
        mock_text_messages = [MagicMock(), MagicMock()]
        mock_mime_text.side_effect = mock_text_messages
        mock_base64.urlsafe_b64encode.return_value.decode.return_value = decoded
        with SAMPLE_TEXT.open() as input_file:
            file_text = input_file.read()

        msg = create_message_with_attachment(
            sender=FROM, to=TO, subject=SUBJECT, message_text=MSG_TEXT, file=SAMPLE_TEXT
        )

        self.assertEqual({"raw": decoded}, msg)
        mock_mime_multipart.assert_called_once()
        calls = [call('to', TO), call('from', FROM), call('subject', SUBJECT)]
        mock_message.__setitem__.assert_has_calls(calls)
        mock_mime_text.assert_has_calls([call(MSG_TEXT), call(file_text, _subtype='plain')])
        mock_text_messages[1].add_header.assert_called_with(
            'Content-Disposition', 'attachment', filename=SAMPLE_TEXT.name
        )
        mock_message.attach.assert_has_calls([
            call(mock_text_messages[0]), call(mock_text_messages[1])
        ])

    @patch('dkutils.gmail_api.gmail_client.MIMEImage')
    @patch('dkutils.gmail_api.gmail_client.MIMEText')
    @patch('dkutils.gmail_api.gmail_client.base64')
    @patch('dkutils.gmail_api.gmail_client.MIMEMultipart')
    def test_create_message_with_attachment_when_image_file(
        self, mock_mime_multipart, mock_base64, mock_mime_text, mock_mime_image
    ):
        self.verify_create_message_with_attachement(
            mock_base64,
            mock_mime_image,
            mock_mime_multipart,
            mock_mime_text,
            attachment=SAMPLE_IMAGE,
            subtype='gif'
        )

    @patch('dkutils.gmail_api.gmail_client.MIMEAudio')
    @patch('dkutils.gmail_api.gmail_client.MIMEText')
    @patch('dkutils.gmail_api.gmail_client.base64')
    @patch('dkutils.gmail_api.gmail_client.MIMEMultipart')
    def test_create_message_with_attachment_when_audio_file(
        self, mock_mime_multipart, mock_base64, mock_mime_text, mock_mime_audio
    ):
        self.verify_create_message_with_attachement(
            mock_base64,
            mock_mime_audio,
            mock_mime_multipart,
            mock_mime_text,
            attachment=SAMPLE_AUDIO,
            subtype='mpeg'
        )

    @patch('dkutils.gmail_api.gmail_client.MIMEBase')
    @patch('dkutils.gmail_api.gmail_client.MIMEText')
    @patch('dkutils.gmail_api.gmail_client.base64')
    @patch('dkutils.gmail_api.gmail_client.MIMEMultipart')
    def test_create_message_with_attachment_when_other_file(
        self, mock_mime_multipart, mock_base64, mock_mime_text, mock_mime_base
    ):
        message_as_byte = bytes('test', 'utf-8')
        mock_message = mock_mime_multipart.return_value
        mock_message.as_bytes.return_value = message_as_byte
        decoded = "decoded"
        mock_base64.urlsafe_b64encode.return_value.decode.return_value = decoded
        with SAMPLE_OTHER.open('rb') as input_file:
            file_text = input_file.read()

        msg = create_message_with_attachment(
            sender=FROM, to=TO, subject=SUBJECT, message_text=MSG_TEXT, file=SAMPLE_OTHER
        )

        self.assertEqual({"raw": decoded}, msg)
        mock_mime_multipart.assert_called_once()
        calls = [call('to', TO), call('from', FROM), call('subject', SUBJECT)]
        mock_message.__setitem__.assert_has_calls(calls)
        mock_mime_text.assert_called_with(MSG_TEXT)
        mock_mime_base.assert_called_with('application', 'octet-stream')
        mock_mime_base.return_value.set_payload.assert_called_with(file_text)
        mock_mime_base.return_value.add_header.assert_called_with(
            'Content-Disposition', 'attachment', filename=SAMPLE_OTHER.name
        )
        mock_message.attach.assert_has_calls([
            call(mock_mime_text.return_value),
            call(mock_mime_base.return_value)
        ])

    def verify_create_message_with_attachement(
        self, mock_base64, mock_mime_type, mock_mime_multipart, mock_mime_text, attachment, subtype
    ):
        message_as_byte = bytes('test', 'utf-8')
        mock_message = mock_mime_multipart.return_value
        mock_message.as_bytes.return_value = message_as_byte
        decoded = "decoded"
        mock_base64.urlsafe_b64encode.return_value.decode.return_value = decoded
        with attachment.open('rb') as input_file:
            file_data = input_file.read()
        msg = create_message_with_attachment(
            sender=FROM, to=TO, subject=SUBJECT, message_text=MSG_TEXT, file=attachment
        )
        self.assertEqual({"raw": decoded}, msg)
        mock_mime_multipart.assert_called_once()
        calls = [call('to', TO), call('from', FROM), call('subject', SUBJECT)]
        mock_message.__setitem__.assert_has_calls(calls)
        mock_mime_text.assert_called_with(MSG_TEXT)
        mock_mime_type.assert_called_with(file_data, _subtype=subtype)
        mock_mime_type.return_value.add_header.assert_called_with(
            'Content-Disposition', 'attachment', filename=attachment.name
        )
        mock_message.attach.assert_has_calls([
            call(mock_mime_text.return_value),
            call(mock_mime_type.return_value)
        ])


class TestGmailClient(TestCase):

    @patch('dkutils.gmail_api.gmail_client.build')
    def setUp(self, mock_build):
        self.test_dir = tempfile.TemporaryDirectory()
        self.client = GMailClient({})

    def tearDown(self):
        self.test_dir.cleanup()

    def test_create_base64_encoded_token_when_credentials_path_does_not_exist_then_raises_gmailclientexception(
        self
    ):
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

        mock_installed_app_flow.from_client_secrets_file.assert_called_once_with(
            credentials_file, ['https://www.googleapis.com/auth/gmail.readonly']
        )
        mock_installed_app_flow.from_client_secrets_file.return_value.run_local_server.assert_called_once_with(
            port=0
        )
        mock_pickle.dumps.assert_called_once_with(
            mock_installed_app_flow.from_client_secrets_file.return_value.run_local_server.
            return_value
        )
        self.assertTrue(
            base64_token_file.exists(), f'{base64_token_file.name} should have been created'
        )
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

    def test_send_message_when_no_user_specified_uses_me(self):
        mock_messages = self.setup_mock_messages()

        self.assertEqual(SENT_MESSAGE, self.client.send_message(MESSAGE))

        mock_messages.send.assert_called_with(userId='me', body=MESSAGE)

    def test_send_message_when_user_specified_uses_user(self):
        mock_messages = self.setup_mock_messages()
        user_id = "someone@some.com"

        self.assertEqual(SENT_MESSAGE, self.client.send_message(MESSAGE, user_id=user_id))

        mock_messages.send.assert_called_with(userId=user_id, body=MESSAGE)

    @patch('dkutils.gmail_api.gmail_client.WaitLoop')
    def test_approval_when_response_does_not_approve_returns_false(self, mock_wait_loop):
        mock_wait_loop.return_value = True
        mock_messages = self.setup_mock_messages()
        msg_id = '123'
        mock_list = mock_messages.list
        mock_list.return_value.execute.return_value = {'messages': [{'id': msg_id}]}
        mock_get = mock_messages.get
        mock_get.return_value.execute.return_value = {'snippet': "stuff"}

        self.assertFalse(self.client.has_approval(subject=SUBJECT))

        mock_list.assert_called_with(userId='me', labelIds=['INBOX'], q=f'subject: {SUBJECT}')
        mock_get.assert_called_with(userId='me', id=msg_id)

    @patch('dkutils.gmail_api.gmail_client.WaitLoop')
    def test_approval_when_timeout_without_getting_response(self, mock_wait_loop):
        mock_wait_loop.return_value.__bool__.side_effect = [True, False]
        mock_messages = self.setup_mock_messages()
        mock_list = mock_messages.list
        mock_list.return_value.execute.return_value = {'messages': []}

        self.assertFalse(self.client.has_approval(subject=SUBJECT))

        mock_list.assert_called_with(userId='me', labelIds=['INBOX'], q=f'subject: {SUBJECT}')

    @patch('dkutils.gmail_api.gmail_client.WaitLoop')
    def test_approval_when_response_has_approval_returns_true(self, mock_wait_loop):
        mock_wait_loop.return_value = True
        mock_messages = self.setup_mock_messages()
        msg_id = '123'
        mock_list = mock_messages.list
        mock_list.return_value.execute.return_value = {'messages': [{'id': msg_id}]}
        mock_get = mock_messages.get
        response_text = f"{GMAIL_APPROVAL_STRING} for use"
        mock_get.return_value.execute.return_value = {'snippet': response_text}

        self.assertTrue(self.client.has_approval(subject=SUBJECT))

        mock_list.assert_called_with(userId='me', labelIds=['INBOX'], q=f'subject: {SUBJECT}')
        mock_get.assert_called_with(userId='me', id=msg_id)

    def setup_mock_messages(self):
        mock_service = self.client.service
        mock_users = mock_service.users.return_value
        mock_messages = mock_users.messages.return_value
        mock_send = mock_messages.send.return_value
        mock_send.execute.return_value = SENT_MESSAGE
        return mock_messages
