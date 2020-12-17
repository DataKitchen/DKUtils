"""Client to handle connections and actions executed against a remote host."""
import collections
import logging

from paramiko import SSHClient, AutoAddPolicy
from paramiko.auth_handler import AuthenticationException
from scp import SCPClient, SCPException

from ..validation import ensure_pathlib

CommandResult = collections.namedtuple('CommandResult', 'status stdin stdout stderr')
"""A namedtuple containing the results of command execution

Attributes
----------
status: int
    which contains an integer the exit code of the process on the server. Normally this should be 0
stdin: file-like
    a file-like object representing the stdin for the command
stdout: file-like
    a file-like object representing the stdout for the command
stderr: file-like
    a file-like object representing the stderr for the command

"""


class RemoteClient:

    def __init__(self, host, user, password=None, key_filename=None, logger=None):
        """
        Client to interact with a remote host via SSH & SCP.

        Parameters
        ----------
        host: str
            the server to connect to
        user: str
            the username to authenticate as
        password: str, optional
            used for password authentication
        key_filename: str, optional
            the file name of the pem file to be used for authentication
        logger: Python logger, optional
            python logger
        """
        self._host = host
        self._user = user
        self._password = password
        self._client = None
        self._scp = None
        self._conn = None
        self._key_filename = key_filename
        self._logger = logger if logger else logging.getLogger(__name__)

    def _connect(self):
        """
        Open connection to remote host.

        Raises
        ------
        AuthenticationException
            If authentication fails
        """
        if self._client is None:
            try:
                client = SSHClient()
                client.set_missing_host_key_policy(AutoAddPolicy())
                client.connect(
                    self._host,
                    username=self._user,
                    password=self._password,
                    look_for_keys=True,
                    timeout=5000,
                    key_filename=self._key_filename
                )
                self._client = client
                self._scp = SCPClient(self._client.get_transport())
            except AuthenticationException as error:
                self._logger.error(f'Authentication failed:  {error}')
                raise error

    def execute_commands(self, commands, stream_logs=False):
        """
        Execute multiple commands in succession.

        Parameters
        ----------
        commands : List(str)
            List of commands as strings
        stream_logs: Boolean, optional
            Stream logs to python logger - this exhausts stdout

        Returns
        -------
        list of CommandResult

        Examples
        --------
        >>> from dkutils.ssh.remote_client import RemoteClient
        ... HOST = "ec2-107-23-93-203.compute-1.amazonaws.com"
        ... USER = "ec2-user"
        ... key_filename = 'some.pem'
        ... client = RemoteClient(HOST, USER, key_filename=key_filename)
        ... result = client.execute_commands(['ls /'])[0]
        ... if result.status != 0:
        ...     for line in result.stderr:
        ...         print(line.rstrip())
        ... else:
        ...     for line in result.stdout:
        ...        print(line.rstrip())

        """
        self._connect()
        results = []
        for command in commands:
            if stream_logs:
                stdin, stdout, stderr = self._client.exec_command(command, get_pty=True)
                for line in iter(lambda: stdout.readline(2048), ""):
                    self._logger.info(line.rstrip())
            else:
                stdin, stdout, stderr = self._client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            result = CommandResult(exit_code, stdin=stdin, stdout=stdout, stderr=stderr)
            results.append(result)
        return results

    def bulk_upload(self, remote_path, files):
        """
        Upload multiple files to a remote directory.

        Parameters
        ----------
        remote_path: str or pathlib.PurePath
            The directory to upload files to on the server
        files : List(str)
            List of local file paths to be uploaded
        """
        remote_path = ensure_pathlib(remote_path)
        self._connect()
        for file in files:
            self.__upload_single_file(remote_path, file)
        self._logger.debug(
            f'Finished uploading {len(files)} files to {remote_path} on {self._host}'
        )

    def __upload_single_file(self, remote_path, file):
        """
        Upload a single file to a remote directory.

        Parameters
        ----------
        remote_path: pathlib.PurePath
            Remote path where file is uploaded
        file: str
            Local path to file being uploaded

        Raises
        ------
        SCPException
            If an exception occurs uploading the file
        """
        try:
            self._scp.put(file, recursive=True, remote_path=str(remote_path))
        except SCPException as error:
            self._logger.error(error)
            raise error
        self._logger.debug(f'Uploaded {file} to {remote_path}')

    def bulk_download(self, remote_path, files, local_path=''):
        """
        Download multiple files from remote directory.

        Parameters
        ----------
        remote_path: str or pathlib.PurePath
            Target directory on the server from which to download files
        files : List(str)
            List of remote filenames to be downloaded
        local_path : str or pathlib.PurePath, optional
            Local destination directory of downloaded files
        """
        remote_path = ensure_pathlib(remote_path)
        local_path = ensure_pathlib(local_path)
        if not local_path.is_dir():
            raise NotADirectoryError(f'Local path is not a directory: {local_path}')
        self._connect()
        for file in files:
            self.__download_single_file(remote_path / file, local_path)
        self._logger.debug(
            f'Finished downloading {len(files)} files from {remote_path} on {self._host}'
        )

    def __download_single_file(self, remote_path, local_path):
        """
        Download a single file from a remote directory.

        Parameters
        ----------
        remote_path: pathlib.PurePath
            Path of the remote file or directory to be downloaded
        local_path: pathlib.PurePath
            Local destination directory of downloaded file

        Raises
        ------
        SCPException
            If an exception occurs downloading the file/directory
        """
        try:
            self._scp.get(str(remote_path), local_path=str(local_path), recursive=True)
        except SCPException as error:
            self._logger.error(error)
            raise error
        self._logger.debug(
            f'Downloaded {remote_path.name} from {remote_path.parent} to {local_path}'
        )

    def disconnect(self):
        """
        Close SSH & SCP connection.
        """
        if self._client:
            self._client.close()
        if self._scp:
            self._scp.close()
