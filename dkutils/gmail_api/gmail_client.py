import base64
import os
import pickle
from enum import Enum
from pathlib import Path
from typing import List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GmailClientException(Exception):
    pass


class Scope(Enum):

    def __new__(cls, value, description):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    LABELS = (
        'https://www.googleapis.com/auth/gmail.labels',
        'Create, read, update, and delete labels only.'
    )
    SEND = (
        'https://www.googleapis.com/auth/gmail.send',
        'Send messages only. No read or modify privileges on '
        'mailbox.'
    )
    READ_ONLY = (
        'https://www.googleapis.com/auth/gmail.readonly',
        'Read all resources and their metadata—no write '
        'operations.'
    )
    COMPOSE = (
        'https://www.googleapis.com/auth/gmail.compose',
        'Create, read, update, and delete drafts. Send '
        'messages and drafts.'
    )
    INSERT = ('https://www.googleapis.com/auth/gmail.insert', 'Insert and import messages only.')
    MODIFY = (
        'https://www.googleapis.com/auth/gmail.modify',
        'All read/write operations except immediate, permanent'
        ' deletion of threads and messages, bypassing Trash.'
    )
    METADATA = (
        'https://www.googleapis.com/auth/gmail.metadata',
        'Read resources metadata including labels, history'
        ' records, and email message headers, but not '
        'the message body or attachments.'
    )
    BASIC = ('https://www.googleapis.com/auth/gmail.settings.basic', 'Manage basic mail settings.')
    SHARING = (
        'https://www.googleapis.com/auth/gmail.settings.sharing',
        'Manage sensitive mail settings, including '
        'forwarding rules and aliases.'
        'Note:Operations guarded by this scope '
        'are restricted to administrative use '
        'only. They are only available to Google '
        'Workspace customers using a service '
        'account with domain-wide delegation.'
    )
    FULL = (
        'https://mail.google.com/',
        'Full access to the account’s mailboxes, including permanent deletion of '
        'threads and messages This scope should only be requested if your '
        'application needs to immediately and permanently delete threads and '
        'messages, bypassing Trash; all other actions can be performed with less '
        'permissive scopes.'
    )


SCOPES = [Scope.READ_ONLY]


def create_base64_encoded_token(
    credentials_path: Path, token_path: Path, scopes: List[Scope] = SCOPES
):
    """
    This will use the provided Path for the json.credentials file and create a token with the scopes
    provided and base64 encode it at the path specified. The base64 encoded file can then be loaded into vault for
    use by other methods in this library. When you run this function keep in mind that a browser window will be opened
    for you to authorize access.

    Parameters
    ----------
    credentials_path: Path
        the path to the file containing the credentials. To create this file follow the instructions
        found at https://developers.google.com/gmail/api/quickstart/python Under Step1: Turn on the GMAIL API
    token_path: Path
        the path to the file that will contain the base64 encoded token that can uploaded to vault.
    scopes: list, optional
        a list containing the requested scopes. See https://developers.google.com/gmail/api/auth/scopes
        for a list of the scopes. Will default to [Scope.READ_ONLY]
    """
    if not credentials_path.exists():
        raise GmailClientException("Credentials file must exist")
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path, [scope.value for scope in scopes]
    )
    credentials = flow.run_local_server(port=0)
    pickled_credentials = pickle.dumps(credentials)
    with token_path.open("wb") as output:
        output.write(base64.b64encode(pickled_credentials))


def get_object_from_environment(environment_variable_name):
    """
    This function will get an object that has been pickled and base64 encoded from an environment variable with the
    specified name. This was intended to be used for retrieving the credentials for using the GMail API from an
    environment variable but it can be used to retrieve any python object that has been pickled and base64 encoded
    as an environment variable.

    Parameters
    ----------
    environment_variable_name: str
        a string specifying the name of the environment variable containing the object.

    Returns
    -------
        object
    """
    encoded = os.getenv(environment_variable_name)
    decoded = base64.b64decode(encoded)
    return pickle.loads(decoded)


class GMailClient:

    def __init__(self, credentials: Credentials):
        """
        Client object for access the GMail API.
        the create_base64_encoded_token function can be used to initially create a set of credentials which are
        base64 encoded in a file that can be looded into vault. This value from vault can then be used as an
        environment variable in a variation. The get_object_from_environment can be used to reconstitute the
        credentials from the environment variable. Soo
        Parameters
        ----------
        credentials: Credentials
            the credentials needed to access the API
        """
        self.service = build('gmail', 'v1', credentials=credentials)
