import logging
from dataclasses import dataclass, is_dataclass
from datetime import datetime
from enum import Enum
from typing import List

import dateutil.parser as date_parser
import requests
from requests_oauthlib import OAuth1

from dkutils.wait_loop import WaitLoop

logger = logging.getLogger(__name__)


class GalleryException(Exception):
    pass


def nested_dataclass_decorator(*args, **kwargs):
    """
    Returns
    -------
    A decorator that can be used on dataclasses that contain nested dataclasses. Use of this decorator on a dataclass
    which contains a field that is also a dataclass will allow the class to be instantiated via a dictionary which
    also contains a nested dictionary for the the field that is a dataclass. For example if you had the following
    declaration:
    @dataclass
    class A:
        a: int
        b: str

    @dataclass
    class B:
        c: str
        d: A

    You would normally need to construct an instance of Class B as follows:
    a = A({"a": 1, "b": "one"})
    b = B({"c": "see", "d": a})
    You need to construct an instance of A before creating B. Using this decorator on B will instead let you do the
    following:
    b = B({"c": "see", "d": {"a": 1, "b": "one"}}
    """

    def wrapper(check_class):
        check_class = dataclass(check_class, **kwargs)
        original_init = check_class.__init__

        def __init__(self, *args, **kwargs):
            for name, value in kwargs.items():
                field_type = check_class.__annotations__.get(name, None)
                if is_dataclass(field_type) and isinstance(value, dict):
                    obj = field_type(**value)
                    kwargs[name] = obj
                original_init(self, *args, **kwargs)

        check_class.__init__ = __init__
        return check_class

    return wrapper(args[0]) if args else wrapper


class JobInfoStatus(Enum):

    def __new__(cls, value, description):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    INFO = (1, 'Status Message: Information')
    WARNING = (2, 'Status Message: Warning')
    ERROR = (3, 'Status Message: Error')
    COMPLETE = (4, 'The tool has completed its processing')
    FIELD_CONVERSION_ERROR = (5, 'Status Message: Field Conversion Error')
    FIELD_CONVERSION_ERROR_LIMIT = (6, 'The field conversion error limit has been reached')
    DISABLED = (7, 'output tools have been disabled')
    FILE_INPUT = (8, 'Input file of this tool')
    FILE_OUTPUT = (9, 'Output file of this tool')
    UPDATE_OUTPUT_META_INFO_XML = (10, 'XML that is the updated meta info for this tool.')
    UPDATE_OUTPUT_CONFIG_XML = (11, 'XML that is the configuration for this tool.')
    REQUEST_AUTO_CONFIG_REFRESH = (
        12, 'This will cause the config to refresh in the GUI with no user interaction '
        'typically this is done when the tool is already in an error state, but maybe '
        'the gui can fix it with no user interaction.'
    )
    DOCUMENT_TEMP_FILE = (13, 'Usually a browse.')
    TEMP_DIRECTORY = (14, 'the directory of %Temp%')
    FILE_DEPENDENCY = (
        15,
        'the dependent files associated with a compound file - Status_File_Output has the main file to '
        'link to this has the main file (fully pathed) | fully pathed dependent file | fully pathed '
        'dependent file | etc'
    )
    CACHE_TEMP_FILE = (16, 'A temporary file for caching data between runs.')
    APPEND_OR_UPDATE_OUTPUT_CONFIG_XML = (
        18, 'append something to the XML config data for this tool, or update an existing node.'
    )
    CONNECT_INFO_XML = (17, 'XML that is the Connection information for this tool.')
    LOW_DISK_WARNING = (
        20,
        'This will tell the user that the free disk space is running low and pause the module untile the user responds'
    )
    SAFE_MODE_ERROR = (21, 'STATUS_RestrictedDataSetError 22')
    CHOOSE_FROM_MULTIPLE = (
        30, "This will present the user with a choice of results. It is typically used for the "
        "geocoder for a multiple match but there is no reason it couldn't be used by any tool.The "
        "Message value is a \n delimited list of strings.The 1st string is the question that will "
        "be at the top of the dialog.The following are the choices that the user can pick from -1 "
        "for cancel\nreturn is -2\nfor 1st to all, -3 for none to all 0 for none, 1...N for a "
        "specific value"
    )
    PREVIEW_FAIL = (31, 'In preview mode send PREVIEW_FAIL if not supported')
    OUTPUT_FIELDNAMES = (40, 'The field names for this SRCT output tool.')
    OUTPUT_RECORD = (41, 'The record (comma separated, quoted) for this SRCT output tool.')
    RECORD_COUNT_AND_SIZE = (
        50, 'Indicates the number and size of records output by the tool so far. The string will '
        'be in the format: "OutputName|RecordCount\nTotalSize"'
    )
    BROWSE_EVERY_WHERE_FILENAME = (
        70, 'The FileName of the temporary yxbe file containing the Browse Everywhere data'
        ' for this run.'
    )
    BROWSE_EVERYWHERE_FILENAME_EX = (
        71, 'The FileName of the temporary yxbe file containing the Browse Everywhere '
        'data for e1 in e2 for this run.'
    )
    SHARED_ASSET_CREATED = (90, 'STATUS_SharedAssetRequested 91')
    RELEASE_ASSET_REQUESTED = (92, 'STATUS_DisplayCustomDialog 99')
    INSIGHT_UPDATE = (100, 'Indicates an insight needs to be updated on the gallery.')


@dataclass
class JobInfoMessage:
    status: int
    text: str
    toolId: int


@nested_dataclass_decorator
class JobInfo:
    id: str
    appId: str
    createDate: datetime
    status: str
    disposition: str
    outputs: dict
    messages: List[JobInfoMessage]
    priority: int
    workerTag: str
    runWithE2: bool

    def __post_init__(self):
        self.createDate = date_parser.parse(self.createDate)
        for index, message in enumerate(self.messages):
            if isinstance(message, dict):
                message = JobInfoMessage(**message)
                self.messages[index] = message


@dataclass
class MetaInfo:
    name: str
    description: str
    author: str
    copyright: str
    url: str
    urlText: str
    outputMessage: str
    noOutputFilesMessage: str


@nested_dataclass_decorator
class Workflow:
    id: str
    subscriptionId: str
    public: bool
    runDisabled: bool
    packageType: str
    uploadDate: str
    fileName: str
    metaInfo: MetaInfo
    isChained: bool
    version: int
    runCount: int
    workerTag: str
    isE2: bool


class GalleryClient:
    """
        Client object for invoking calls to the Alteryx Gallery API. See https://gallery.alteryx.com/api-docs/ for more
        information

        Parameters
        ----------
        api_location : str
            The base URL for the Gallery server
        api_key : str
            The api key used to authenticate access to the Gallery API. Then can be found in the Keys section of
            account settings on the Alteryx Gallery.
        api_secret: str
            The api secret used to authenticate access to the Gallery API. Then can be found in the Keys section of
            account settings on the Alteryx Gallery.
        """

    def __init__(self, api_location: str, api_key: str, api_secret: str) -> None:
        self.api_location = api_location
        self.api_key = api_key
        self.api_secret = api_secret

    @property
    def api_location(self):
        return self._api_location

    @api_location.setter
    def api_location(self, api_location: str):
        if not api_location:
            raise GalleryException("'api_location' cannot be empty")
        self._api_location = api_location

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, key: str):
        if not key:
            raise GalleryException("'api_key' cannot be empty")
        self._api_key = key

    @property
    def api_secret(self):
        return self._api_secret

    @api_secret.setter
    def api_secret(self, secret_key: str):
        if not secret_key:
            raise GalleryException("'api_secret' cannot be empty")
        self._api_secret = secret_key

    def _get(self, suffix, params=None, **kwargs):
        """
        Sends a GET request

        Parameters
        ----------
        suffix:str
            Path for the API call
        params:dict, optional
            List of tuples or bytes to send in the query string for the Request.
        kwargs
            Optional arguments that request takes.

        Raises
        ------
        HTTPError
            if one occurred.

        Returns
        -------
        object
            An object deserialized from the JSON returned in the response

        """
        response = requests.get(
            self.api_location + suffix, auth=self._get_authentication(), params=params, **kwargs
        )
        response.raise_for_status()
        return response.json()

    def _post(self, suffix, params=None, **kwargs):
        """
        Sends a POST request

        Parameters
        ----------
        suffix:str
            Path for the API call
        params:dict, optional
            List of tuples or bytes to send in the query string for the Request.
        kwargs
            Optional arguments that request takes.

        Raises
        ------
        HTTPError
            if one occurred.

        Returns
        -------
        object
            An object deserialized from the JSON returned in the response

        """
        response = requests.post(
            self.api_location + suffix, auth=self._get_authentication(), params=params, **kwargs
        )
        response.raise_for_status()
        return response.json()

    def _get_authentication(self):
        """

        Returns
        -------
        OAuth1
            An object that can be used to sign a request using OAuth 1 (RFC5849)

        """
        return OAuth1(self._api_key, self._api_secret)

    def get_subscription_workflows(self) -> List[Workflow]:
        """

        Returns
        -------
        list or None
            A list of workflows

        Notes
        -----
        Subscription is tied to API key. You cannot request workflows for any other subscription without that
        subscription's key.
        """
        workflows_list = self._get("/v1/workflows/subscription/")
        return [Workflow(**workflow) for workflow in workflows_list]

    def get_all_workflows(self) -> List[Workflow]:
        """

        Returns
        -------
        list or None
            A list of all workflows

        Notes
        -----
        Only Gallery Curators(Admins) can use this API endpoint.
        """
        workflows_list = self._get("/admin/v1/workflows/all/")
        return [Workflow(**workflow) for workflow in workflows_list]

    def execute_workflow(self, app_id: str) -> JobInfo:
        """
        Queue an app execution job.

        Returns
        -------
        JobInfo
            Information about the job
        """
        job_info = self._post(f"/v1/workflows/{app_id}/jobs/")
        return JobInfo(**job_info)

    def execute_workflow_and_wait(
            self, app_id: str, sleep_seconds: int = 300, max_wait_seconds: int = 3
    ) -> JobInfo:
        """
        Queue an app execution job and wait for the job to complete.

        Raises
        ------
        GalleryException
            if job times out
        Returns
        -------
        JobInfo
            Information about the job
        """
        job_info: JobInfo = self.execute_workflow(app_id=app_id)
        job_id = job_info.id
        wait = WaitLoop(sleep_seconds, max_wait_seconds)
        while wait:
            if job_info.status != 'Completed':
                job_info = self.get_job_status(job_id)
                logger.info(f'Current status: {job_info.status}')
            else:
                return job_info
        raise GalleryException(f'Timed out after: {max_wait_seconds} seconds')

    def get_job_status(self, job_id: str) -> JobInfo:
        """
        Retrieves the job and its current state

        Returns
        -------
        JobInfo
            Information about the job and its current state
        """
        job_info = self._get(f"/v1/jobs/{job_id}/")
        return JobInfo(**job_info)
