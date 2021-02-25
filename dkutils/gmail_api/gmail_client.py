import base64
import logging
import mimetypes
import os
import pickle
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from dkutils.constants import GMAIL_APPROVAL_STRING, GMAIL_SLEEP_SECONDS, GMAIL_MAX_WAIT_SECONDS
from dkutils.wait_loop import WaitLoop

logger = logging.getLogger(__name__)


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
    credentials_path : Path
        The path to the file containing the credentials. To create this file follow the instructions
        found at https://developers.google.com/gmail/api/quickstart/python Under Step1: Turn on the
        GMAIL API
    token_path : Path
        The path to the file that will contain the base64 encoded token that can uploaded to vault.
    scopes : list, optional
        A list containing the requested scopes. See https://developers.google.com/gmail/api/auth/scopes
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
    This function will get an object that has been pickled and base64 encoded from an environment
    variable with the specified name. This was intended to be used for retrieving the credentials
    for using the GMail API from an environment variable but it can be used to retrieve any python
    object that has been pickled and base64 encoded as an environment variable.

    Parameters
    ----------
    environment_variable_name : str
        A string specifying the name of the environment variable containing the object.

    Returns
    -------
        object
    """
    encoded = os.getenv(environment_variable_name)
    decoded = base64.b64decode(encoded)
    return pickle.loads(decoded)


def create_message(sender, to, subject, message_text):
    """
    Create a message for an email.

    Parameters
    ----------
    sender : str
        Email address of the sender.
    to : str
        Email address of the receiver.
    subject : str
        The subject of the email message.
    message_text : str
        The text of the email message.

    Returns
    -------
    object
        An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
    b64_string = b64_bytes.decode()
    return {'raw': b64_string}


def create_message_with_attachment(sender, to, subject, message_text, file):
    """
    Create a message for an email.

    Parameters
    ----------
    sender : str
        Email address of the sender.
    to : str
        Email address of the receiver.
    subject : str
        The subject of the email message.
    message_text : str
        The text of the email message.
    file : str
        The path to the file to be attached.

    Returns
    -------
    object
        An object containing a base64url encoded email object.
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    content_type, encoding = mimetypes.guess_type(file)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    maintype, subtype = content_type.split('/', 1)
    if maintype == 'text':
        with open(file) as fp:
            # Note: we should handle calculating the charset
            msg = MIMEText(fp.read(), _subtype=subtype)
    elif maintype == 'image':
        with open(file, 'rb') as fp:
            msg = MIMEImage(fp.read(), _subtype=subtype)
    elif maintype == 'audio':
        with open(file, 'rb') as fp:
            msg = MIMEAudio(fp.read(), _subtype=subtype)
    elif maintype == 'application':
        with open(file, 'rb') as fp:
            msg = MIMEApplication(fp.read(), _subtype=subtype)
    else:
        with open(file, 'rb') as fp:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(fp.read())
    filename = os.path.basename(file)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)
    b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
    b64_string = b64_bytes.decode()
    return {'raw': b64_string}


class GMailClient:

    def __init__(self, credentials: Credentials):
        """
        Client object for access the GMail API. The create_base64_encoded_token function can be
        used to initially create a set of credentials which are base64 encoded in a file that can
        be looded into vault. This value from vault can then be used as an environment variable in
        a variation. The get_object_from_environment can be used to reconstitute the credentials
        from the environment variable.

        Parameters
        ----------
        credentials : Credentials
            the credentials needed to access the API
        """
        self.service = build('gmail', 'v1', credentials=credentials)

    def send_message(self, message, user_id='me'):
        """
        Send an email message.

        Parameters
        ----------
        message : str
            The message to be sent
        user_id : str, optional
            User's email address. The special value "me" will be used to indicate the authenticated
            user if no value is provided

        Returns
        -------
        dict
            The sent message
        """

        message = (self.service.users().messages().send(userId=user_id, body=message).execute())
        logger.debug(f'Message Id: {message["id"]}')
        return message

    def has_approval(
        self,
        subject,
        approval_string=GMAIL_APPROVAL_STRING,
        sleep_seconds=GMAIL_SLEEP_SECONDS,
        max_wait=GMAIL_MAX_WAIT_SECONDS
    ):
        """
        This function can be used to determine if a response has been received containing the
        specified approval string. The given subject is used to retrieve messages of interest. This
        function will poll for new email every sleep seconds until the max wait seconds have been
        exceeded.

        Parameters
        ----------
        subject : str
            The subject to use to retrieve messages from the inbox
        approval_string : str, opt
            If the message body of a message retrieved starts with the given string True will be
            returned by the function indicating that approval has been received. Will default to
            Approved if not specified
        sleep_seconds : int, opt
            Number of seconds to wait between retrieving email. If not specified will default to 10
        max_wait : int, opt
            The maximum number of seconds to wait for approval to be recieved. If not specified
            will default to 30

        Returns
        -------
        bool
            True or False with True indicating that approval has been received
        """
        wait_loop = WaitLoop(sleep_seconds, max_wait)
        while wait_loop:
            results = self.service.users().messages().list(
                userId='me', labelIds=['INBOX'], q=f'subject: {subject}'
            ).execute()
            messages = results.get('messages', [])
            if messages:
                for message in messages:
                    msg = self.service.users().messages().get(
                        userId='me', id=message['id']
                    ).execute()
                    logger.info(f'Email reply received: {msg["snippet"]}')
                    return msg['snippet'].lower().startswith(approval_string.lower())
        logger.warn("No reply was found")
        return False
