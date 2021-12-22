import mimetypes
from email.message import EmailMessage
from email.utils import COMMASPACE
from smtplib import SMTP
import os


def _convert_to_strings(list_of_strs):
    return (
        COMMASPACE.join(list_of_strs) if isinstance(list_of_strs, (list, tuple)) else list_of_strs
    )


def create_message(
    sender, recipients, subject, plain_text=None, html_text=None, files=None, reply_addresses=None
):
    """
        Create a message for an email.

        Parameters
        ----------
        sender : str
            Email address of the sender.
        recipients : str|list
            Email address(es) of the receiver.
        subject : str
            The subject of the email message.
        plain_text : str
            The plain text of the email message.
        html_text: str
            The html text of the email message.
        files : str|list
            The path(s) of the file(s) to be attached.
        reply_addresses: str|list
            Email address(es) replies should be sent to

        Returns
        -------
        EmailMessage
            An EmailMessage that can be sent
        """
    if not plain_text and not html_text:
        raise TypeError("Either plain_text or html_text is required")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = _convert_to_strings(recipients)
    if reply_addresses:
        message["Reply-To"] = _convert_to_strings(reply_addresses)
    if plain_text:
        message.set_content(plain_text)
    if html_text:
        message.make_alternative()
        message.add_attachment(html_text, 'html')
    if files:
        if isinstance(files, str):
            files = [files]
        for file_path in files:
            filename = os.path.basename(file_path)
            content_type, encoding = mimetypes.guess_type(file_path)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            maintype, subtype = content_type.split('/', 1)
            with open(file_path, 'rb') as fp:
                data = fp.read()
            message.add_attachment(
                data, maintype=maintype, subtype=subtype, filename=filename, cid=f"<{filename}>"
            )

    return message


class SMTP_Sender():
    """
        Class that can send emails using SMTP.

        Parameters
        ----------
        host:str
            The hostname of the SMTP server
        user:str
            The username to login to SMTP server
        password: str
            The password to be used to login to the SMTP server
        port:int
            The port of the SMTP server
        use_tls: bool
            A boolean indicating whether or not to use TLS in communications with the server
        """

    def __init__(self, host, user, password, port=587, use_tls=True):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.use_tls = use_tls

    def do_send(self, message):
        """
        Send an email message via SMTP
        Parameters
        ----------
        message:EmailMessage
            An email message to be sent

        """
        with SMTP(self.host, self.port) as server:
            if self.use_tls:
                server.starttls()
            if self.user and self.password:
                server.login(self.user, self.password)
            server.send_message(message)
