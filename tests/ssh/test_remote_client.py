import os

from unittest import TestCase
from unittest.mock import patch, call, MagicMock

from paramiko.auth_handler import AuthenticationException
from scp import SCPException

from dkutils.ssh.remote_client import RemoteClient, CommandResult

HOST = "somewhere.com"
USER = "Bob"
PASSWORD = "secret"
REMOTE_PATH = "/home/base"


class TestRemoteClient(TestCase):

    def setUp(self):
        self.client = RemoteClient(HOST, USER, PASSWORD)

    def test_constructor(self):
        client = RemoteClient(HOST, USER, PASSWORD)
        self.assertEqual(HOST, client._host)
        self.assertEqual(USER, client._user)
        self.assertEqual(PASSWORD, client._password)

    @patch('dkutils.ssh.remote_client.SCPClient')
    @patch('dkutils.ssh.remote_client.AutoAddPolicy')
    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_connect(self, mock_ssh_client, mock_auto_add_policy, mock_scp_client):
        mock_scp_client.return_value = mock_scp_client
        mock_auto_add_policy.return_value = mock_auto_add_policy
        mock_ssh_client.return_value = mock_ssh_client
        self.client._connect()
        mock_ssh_client.assert_called_once()
        mock_ssh_client.set_missing_host_key_policy.assert_called_once_with(mock_auto_add_policy)
        mock_ssh_client.connect.assert_called_once_with(
            HOST,
            key_filename=None,
            look_for_keys=True,
            password=PASSWORD,
            timeout=5000,
            username=USER
        )
        mock_scp_client.assert_called_once()
        self.assertEqual(self.client._client, mock_ssh_client)
        self.assertEqual(self.client._scp, mock_scp_client)

    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_connect_when_authentication_error(self, mock_ssh_client):
        expected_exception = AuthenticationException("bad juju")
        mock_ssh_client.side_effect = expected_exception
        with self.assertRaises(AuthenticationException) as cm:
            self.client._connect()
        self.assertEqual(expected_exception, cm.exception)

    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_execute_commands(self, mock_ssh_client):
        mock_ssh_client.return_value = mock_ssh_client
        stdin = MagicMock()
        stdout = MagicMock()
        status = 0
        stdout.channel.recv_exit_status.return_value = status
        stderr = MagicMock()
        command_result = CommandResult(status=status, stdin=stdin, stdout=stdout, stderr=stderr)
        mock_ssh_client.exec_command.return_value = (stdin, stdout, stderr)
        commands = ["command1", "command2"]
        self.assertEqual([command_result, command_result], self.client.execute_commands(commands))
        calls = [call(command) for command in commands]
        mock_ssh_client.exec_command.assert_has_calls(calls)
        stdout.channel.recv_exit_status.has_calls(call(), call())

    @patch('dkutils.ssh.remote_client.SCPClient')
    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_bulk_upload(self, mock_ssh_client, mock_scp_client):
        files = ['file1', 'file2']
        mock_scp_client.return_value = mock_scp_client
        self.client.bulk_upload(REMOTE_PATH, files)
        calls = [call(file, recursive=True, remote_path=REMOTE_PATH) for file in files]
        mock_scp_client.put.assert_has_calls(calls)

    @patch('dkutils.ssh.remote_client.SCPClient')
    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_bulk_upload_when_scpexception_raised(self, mock_ssh_client, mock_scp_client):
        expected_exception = SCPException("bad news")
        mock_scp_client.return_value = mock_scp_client
        mock_scp_client.put.side_effect = expected_exception
        with self.assertRaises(SCPException) as cm:
            file = 'file'
            self.client.bulk_upload(REMOTE_PATH, [file])
        self.assertEqual(expected_exception, cm.exception)
        mock_scp_client.put.assert_called_with(file, recursive=True, remote_path=REMOTE_PATH)

    @patch('dkutils.ssh.remote_client.SCPClient')
    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_bulk_disconnect(self, mock_ssh_client, mock_scp_client):
        mock_ssh_client.return_value = mock_ssh_client
        mock_scp_client.return_value = mock_scp_client
        self.client._connect()
        self.client.disconnect()
        mock_ssh_client.close.assert_called_once()
        mock_scp_client.close.assert_called_once()

    @patch('dkutils.ssh.remote_client.SCPClient')
    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_bulk_download(self, _, mock_scp_client):
        files = ['file1', 'file2']
        mock_scp_client.return_value = mock_scp_client
        self.client.bulk_download(REMOTE_PATH, files)
        calls = [
            call(os.path.join(REMOTE_PATH, file), local_path='.', recursive=True) for file in files
        ]
        mock_scp_client.get.assert_has_calls(calls)

    @patch('dkutils.ssh.remote_client.SCPClient')
    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_bulk_download_when_scpexception_raised(self, _, mock_scp_client):
        expected_exception = SCPException("bad news")
        mock_scp_client.return_value = mock_scp_client
        mock_scp_client.get.side_effect = expected_exception
        with self.assertRaises(SCPException) as cm:
            file = 'file'
            self.client.bulk_download(REMOTE_PATH, [file])
        self.assertEqual(expected_exception, cm.exception)
        mock_scp_client.get.assert_called_with(
            os.path.join(REMOTE_PATH, file), local_path='.', recursive=True
        )

    @patch('dkutils.ssh.remote_client.SCPClient')
    @patch('dkutils.ssh.remote_client.SSHClient')
    def test_bulk_download_invalid_local_path(self, _, mock_scp_client):
        mock_scp_client.return_value = mock_scp_client
        with self.assertRaises(NotADirectoryError):
            self.client.bulk_download(REMOTE_PATH, ['file'], local_path='foo')
