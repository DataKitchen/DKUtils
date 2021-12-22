import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, call

from dkutils.smtp_api.sender import create_message, SMTP_Sender

SENDER = 'someone@somewhere.com'
RECIPIENT = 'someone_else@somewhere.com'
SUBJECT = 'Something Important'
PLAIN_TEXT = "Some arbitrary message."
HTML_TEXT = "<html><h1>Some Header</h1><p>test</p></html>"
PASSWORD = "somesecret"
HOST = "server.com"


class Test(TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_create_message_when_no_parameters(self):
        with self.assertRaises(TypeError) as cm:
            create_message()
        self.assertEqual(
            "create_message() missing 3 required positional arguments: 'sender', "
            "'recipients', and 'subject'",
            cm.exception.args[0]
        )
    def test_create_message_when_no_plain_text_or_html_text(self):
        with self.assertRaises(TypeError) as cm:
            create_message(SENDER, RECIPIENT, SUBJECT)
        self.assertEqual(
            "Either plain_text or html_text is required",
            cm.exception.args[0],
        )

    def test_create_message_plain_text(self):
        message = create_message(SENDER, RECIPIENT, SUBJECT, PLAIN_TEXT)
        expected_message = f'Subject: {SUBJECT}\n' \
                           f'From: {SENDER}\n' \
                           f'To: {RECIPIENT}\n' \
                           'Content-Type: text/plain; charset="utf-8"\n' \
                           'Content-Transfer-Encoding: 7bit\nMIME-Version: 1.0\n\n' \
                           f'{PLAIN_TEXT}\n'
        self.assertEqual(expected_message, message.as_string())

    @patch('dkutils.smtp_api.sender.EmailMessage')
    def test_create_message_html_text(self, _):
        message = create_message(SENDER, RECIPIENT, SUBJECT, PLAIN_TEXT, HTML_TEXT)

        message.__setitem__.assert_has_calls([
            call('Subject', SUBJECT),
            call('From', SENDER),
            call('To', RECIPIENT)
        ])
        message.set_content.assert_called_once_with(PLAIN_TEXT)
        message.make_alternative.assert_called_once()
        message.add_attachment.assert_called_once_with(HTML_TEXT, 'html')

    @patch('dkutils.smtp_api.sender.EmailMessage')
    def test_create_message_with_attachment(self, _):
        data = "some data"
        file_name = 'file.txt'
        full_file_name = Path(self.test_dir.name) / file_name
        with full_file_name.open("w+") as output_file:
            output_file.write(data)

        message = create_message(SENDER, RECIPIENT, SUBJECT, PLAIN_TEXT, files=str(full_file_name))
        message.__setitem__.assert_has_calls([
            call('Subject', SUBJECT),
            call('From', SENDER),
            call('To', RECIPIENT)
        ])
        message.set_content.assert_called_once_with(PLAIN_TEXT)
        message.add_attachment.assert_called_once_with(
            str.encode(data), maintype='text', subtype='plain', filename=file_name, cid=f"<{file_name}>"
        )

    def test_constructor_with_defaults(self):
        sender = SMTP_Sender(HOST, SENDER, PASSWORD)

        self.assertEqual(sender.host, HOST)
        self.assertEqual(sender.user, SENDER)
        self.assertEqual(sender.password, PASSWORD)
        self.assertEqual(sender.port, 587)
        self.assertTrue(sender.use_tls)

    def test_constructor(self):
        port = 25

        sender = SMTP_Sender(HOST, SENDER, PASSWORD, port, False)

        self.assertEqual(sender.host, HOST)
        self.assertEqual(sender.user, SENDER)
        self.assertEqual(sender.password, PASSWORD)
        self.assertEqual(sender.port, port)
        self.assertFalse(sender.use_tls)

    @patch('dkutils.smtp_api.sender.SMTP')
    def test_do_send_with_tls(self, mock_smtp):
        message = {}

        SMTP_Sender(HOST, SENDER, PASSWORD).do_send(message)

        mock_smtp.assert_called_once_with(HOST, 587)
        mock_smtp.return_value.__enter__.assert_called_once()
        mock_server = mock_smtp.return_value.__enter__.return_value
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(SENDER, PASSWORD)
        mock_server.send_message.assert_called_once_with(message)

    @patch('dkutils.smtp_api.sender.SMTP')
    def test_do_send_without_tls(self, mock_smtp):
        message = {}

        SMTP_Sender(HOST, user=None, password=None, port=25, use_tls=False).do_send(message)

        mock_smtp.assert_called_once_with(HOST, 25)
        mock_smtp.return_value.__enter__.assert_called_once()
        mock_server = mock_smtp.return_value.__enter__.return_value
        mock_server.starttls.assert_not_called()
        mock_server.login.assert_not_called()
        mock_server.send_message.assert_called_once_with(message)
