import logging
import time
import os
from enum import Enum

import requests

logger = logging.getLogger(__name__)

TERMINAL_STATES = {
    "CANCELED", "COMPLETE", "FAILED", "INTERRUPTED", "KILLED", "PARKED", "PAUSED", "SUSPENDED"
}

DEFAULT_VERSION = "v16.0"


def _raise_exception(msg):
    logger.error(msg)
    raise VeevaNetworkException(msg)


def create_veeva_network_subscription_client(
    dns=None,
    username=None,
    password=None,
    subscription_name=None,
    subscription_type=None,
    system_name=None,
    version=None
):
    """
    Create a client that enables you to manage subscriptions that import and export data to
    and from the Veeva Network.

    Parameters
    ----------
    dns : str, opt
        The URL for your API service, if this variable is absent the the value will be obtained
        from the environment variable VEEVA_DNS
    username : str
        The user ID for Network; for example, john.smith@veevanetwork.com. if this variable is
        absent the the value will be obtained from the environment variable VEEVA_USERNAME
    password : str, opt
        The password for the user ID. if this variable is absent the the value will be obtained
        from the environment variable VEEVA_PASSWORD
    system_name : str, opt
        The unique name of the system if this variable is absent the the value will be obtained
        from the environment variable VEEVA_SYSTEM_NAME
    subscription_name : str, opt
        The unique name of the subscription if this variable is absent the the value will be
        obtained from the environment variable VEEVA_SUBSCRIPTION_NAME
    subscription_type : VeevaNetworkSubscriptionType
        Ff this variable is absent then the value will be obtained from the environment variable
        VEEVA_SUBSCRIPTION_TYPE the type of subscription
    version : str, opt
        The API version if this variable is absent the the value will be obtained from the
        environment variable

    Raises
    ------
    HTTPError
        If the request fails
    VeevaNetworkException
        If subscription_type is not VeevaNetworkSubscriptionType.SOURCE or
        VeevaNetworkSubscriptionType.TARGET. If the authorization header is not available

    """
    if not dns:
        dns = os.environ['VEEVA_DNS']
    if not username:
        username = os.environ['VEEVA_USERNAME']
    if not password:
        password = os.environ['VEEVA_PASSWORD']
    if not system_name:
        system_name = os.environ['VEEVA_SYSTEM_NAME']
    if not subscription_name:
        subscription_name = os.environ['VEEVA_SUBSCRIPTION_NAME']
    if not subscription_type:
        subscription_type = VeevaNetworkSubscriptionType[
            os.environ['VEEVA_SUBSCRIPTION_TYPE'].upper()]
    if not version:
        version = os.environ.get("VEEVA_VERSION", DEFAULT_VERSION)
    if subscription_type == VeevaNetworkSubscriptionType.SOURCE:
        return VeevaSourceSubscriptionClient(
            dns=dns,
            username=username,
            password=password,
            subscription_name=subscription_name,
            system_name=system_name,
            version=version
        )
    elif subscription_type == VeevaNetworkSubscriptionType.TARGET:
        return VeevaTargetSubscriptionClient(
            dns=dns,
            username=username,
            password=password,
            subscription_name=subscription_name,
            system_name=system_name,
            version=version
        )
    _raise_exception(
        f"Subscription type must be either VeevaNetworkSubscriptionType.SOURCE or "
        f"VeevaNetworkSubscriptionType.TARGET but was {subscription_type}"
    )


def run_subscription_job(
    dns=None,
    username=None,
    password=None,
    subscription_name=None,
    subscription_type=None,
    system_name=None,
    version=None
):
    """
    This function will run a subscription job and poll until the job has reached a terminal state.

    Parameters
    ----------
    dns : str, opt
        is the URL for your API service, if this variable is absent the the value will be obtained from the
        environment variable VEEVA_DNS
    username : str
        the user ID for Network; for example, john.smith@veevanetwork.com. if this variable is absent the the value will
         be obtained from the environment variable VEEVA_USERNAME
    password : str, opt
        the password for the user ID. if this variable is absent the the value will be obtained from the
        environment variable VEEVA_PASSWORD
    system_name : str, opt
        is the unique name of the system if this variable is absent the the value will be obtained from the
        environment variable VEEVA_SYSTEM_NAME
    subscription_name : str, opt
        is the unique name of the subscription if this variable is absent the the value will be obtained from the
        environment variable VEEVA_SUBSCRIPTION_NAME
    subscription_type : VeevaNetworkSubscriptionType if this variable is absent the the value will be obtained from the
        environment variable VEEVA_SUBSCRIPTION_TYPE
        the type of subscription
    version : str, opt
        is the API version if this variable is absent the the value will be obtained from the
        environment variable

    Raises
    ------
    HTTPError
        If the request fails
    ValueError
        If the job reaches a terminal status other than COMPLETE

    Returns
    -------
    dict
        A dictionary containing the information about the job.
        For a source subscription the will be similar to the following::

            {
               "filesProcessed" : 1,
               "errorCount" : 0,
               "subscriptionName" : "CRM_Import",
               "completed_date" : "2019-12-18T22:42:32.000Z",
               "job_status" : "COMPLETE",
               "job_id" : 10537,
               "jobResultSummary" : {
                  "CUSTOMKEY" : {
                     "total" : 2,
                     "recordsUpdated" : 0,
                     "recordsSkipped" : 2,
                     "newRecordsAdded" : 0,
                     "recordsInvalidated" : 0,
                     "recordsMerged" : 0
                  },
                  "HCP" : {
                     "total" : 1,
                     "recordsUpdated" : 0,
                     "recordsSkipped" : 1,
                     "recordsMerged" : 0,
                     "recordsInvalidated" : 0,
                     "newRecordsAdded" : 0
                  },
                  "ADDRESS" : {
                     "total" : 1,
                     "recordsUpdated" : 0,
                     "recordsSkipped" : 1,
                     "recordsInvalidated" : 0,
                     "newRecordsAdded" : 0,
                     "recordsMerged" : 0
                  }
               },
               "durationInMilliseconds" : 3000,
               "created_date" : "2019-12-18T22:42:29.000Z",
               "subscriptionId" : 117,
               "processedDataSummary" : {
                  "HCP" : 1,
                  "ADDRESS" : 1
               },
               "type" : "MANUAL",
               "dataLoadSummary" : {
                  "ADDRESS" : {
                     "rowsRead" : 1,
                     "rowsParsed" : 1
                  },
                  "HCP" : {
                     "rowsParsed" : 1,
                     "rowsRead" : 1
                  }
               },
               "badRecordCount" : 0,
               "recordCount" : 2,
               "matchSummary" : {
                  "HCP" : {
                     "ACT" : 1,
                     "notMatched" : 0,
                     "ASK" : 0
                  },
                  "HCO" : {
                     "ACT" : 0,
                     "notMatched" : 0,
                     "ASK" : 0
                  }
               },
               "responseStatus" : "SUCCESS"
            }

        For a target source a dictionary similar to the following is returned::

            {
              "responseStatus": "SUCCESS",
              "subscriptionId": 15,
              "subscriptionName": "targetSubscriptionCustomer",
              "durationInMilliseconds": 2000,
              "type": "MANUAL",
              "errorCount": 0,
              "badRecordCount": 0,
              "exportReferenceCount": 0,
              "exportFull": True,
              "exportIncludeReference": False,
              "exportUpdatedChildOnly": False,
              "exportSetSubscriptionStateOnFull": False,
              "exportFormat": "CSV",
              "exportReferenceVersion": "4",
              "exportActiveOnly": False,
              "jobExportCount": {
                "LICENSE": 3961,
                "RELATION": 333,
                "HCO": 819,
                "HCP": 1060,
                "ADDRESS": 1801,
                "EXTERNALKEYS": 8038
              },
              "job_id": 10563,
              "job_status": "COMPLETE",
              "created_date": "2016-11-17T10:58:49.000-08:00",
              "data_revision_first": "0",
              "data_revision_last": "929335226137870335",
              "export_package_path": "export/change_request/targetSubscriptionCustomer/exp_000001C5.zip",
              "total_records_exported": "1879",
              "completed_date": "2016-11-17T10:58:51.000-08:00",
              "export_archive": "individual",
              "exportFormatDelimiter":"|",
              "exportFormatTextQualifier":"\""
            }

    """
    client = create_veeva_network_subscription_client(
        dns=dns,
        username=username,
        password=password,
        subscription_name=subscription_name,
        subscription_type=subscription_type,
        system_name=system_name,
        version=version
    )
    job = client.run_subscription_process()
    return client.retrieve_network_process_job(job)


class VeevaNetworkException(Exception):
    pass


class VeevaNetworkSubscriptionType(str, Enum):
    SOURCE = 'source',
    TARGET = 'target'


class VeevaNetworkClient:

    def __init__(self, dns, username, password, version):
        """
        Create a client for accessing Veeva Network. This class should not be instantiated directly. You should use
        either VeevaSourceSubscriptionClient or VeevaTargetSubscriptionClient

        Parameters
        ----------
        dns : str
            is the URL for your API service
        username : str
            the user ID for Network; for example, john.smith@veevanetwork.com.
        password : str
            the password for the user ID.
        version : str
            is the API version

        Raises
        ------
        HTTPError
            If the request fails
        ValueError
            If the authorization header is not available

        """
        self.base_url = f'https://{dns}/api/{version if version else "v16.0"}/'

        logger.info('VEEVA NETWORK: Attempting Authenticating')
        response = requests.post(
            self.base_url + 'auth', data={
                'username': username,
                'password': password
            }
        )
        response.raise_for_status()

        # The headers are then passed through as a request authorization header
        self.admin_header = {
            'Authorization': response.json().get('sessionId'),
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }

        if self.admin_header['Authorization'] is None:
            _raise_exception('Could not get an authorization header')
        else:
            logger.info('VEEVA NETWORK: Authentication Successful!')


class VeevaSourceSubscriptionClient(VeevaNetworkClient):

    def __init__(
        self, dns, username, password, subscription_name, system_name, version=DEFAULT_VERSION
    ):
        """
        Create a client that enables you to manage source subscriptions that import and export data to
        and from the Veeva Network.

        Parameters
        ----------
        dns : str
            is the URL for your API service
        username : str
            the user ID for Network; for example, john.smith@veevanetwork.com.
        password : str
            the password for the user ID.
        system_name : str
            is the unique name of the system
        subscription_name : str
            is the unique name of the subscription
        version : str
            is the API version

        Raises
        ------
        HTTPError
            If the request fails

        ValueError
            If the authorization header is not available

        """
        self.subscription_name = subscription_name
        self.system_name = system_name
        self.subscription_type = VeevaNetworkSubscriptionType.SOURCE.value
        super().__init__(dns, username, password, version)

    def run_subscription_process(self):
        """
        This API enables you to create a source or target subscription job.
        Note: This API requires system administrator or API-only permissions.

        Raises
        ------
        HTTPError
            If the request fails

        Returns
        -------
        str
            the unique ID of the job generated for the source subscription you specified.

        """
        response = requests.post(
            f'{self.base_url}systems/{self.system_name}/{self.subscription_type}_subscriptions/'
            f'{self.subscription_name}/job',
            headers=self.admin_header
        )
        response.raise_for_status()
        json = response.json()
        status = json['responseStatus']
        if status != 'SUCCESS':
            _raise_exception(
                f"The job could not be started. Status: {status} - {json['responseMessage']}"
            )
        return json.get('job_id')

    def _retrieve_network_process_job(self, job_resp_id, sleep_seconds=5):
        """
        Retrieve the status of a source or target subscription job. This function will poll
        until the job has reached a terminal state.

        Parameters
        ----------
        job_resp_id : str
            is the unique ID of the job you want to retrieve status on
        sleep_seconds : float, optional
            sleep the given number of seconds betweening polling for the job status. The argument
            may be a floating point number for subsecond precision.

        Raises
        ------
        HTTPError
            If the request fails
        ValueError
            If the job reaches a terminal status other than COMPLETE

        Returns
        -------
        dict
            A dictionary containing the information about the job.

        """
        while True:
            response = requests.get(
                f'{self.base_url}systems/{self.system_name}/{self.subscription_type}_subscriptions/'
                f'{self.subscription_name}/job/{job_resp_id}',
                headers=self.admin_header
            )
            response.raise_for_status()
            json = response.json()
            status = json['responseStatus']
            if status != 'SUCCESS':
                _raise_exception(
                    f"The job status could not be retrieved. Status: {status} - {json['errorType']}"
                )
            job_status = json.get('job_status')
            if job_status not in TERMINAL_STATES:
                logger.info(job_status)
                time.sleep(sleep_seconds)
            else:
                if job_status == 'SUSPENDED':
                    _raise_exception(
                        "VEEVA NETWORK: The job is scheduled and is waiting for shared resources prior to "
                        "becoming active."
                    )
                if job_status == 'COMPLETE':
                    break
                _raise_exception(f'The job has terminated with an unexpected status: {job_status}')
        return response.json()

    def retrieve_network_process_job(self, job_resp_id):
        """
        Retrieve the status of a source or target subscription job. This function will poll
        until the job has reached a terminal state.

        Parameters
        ----------
        job_resp_id : str
            is the unique ID of the job you want to retrieve status on

        Raises
        ------
        HTTPError
            If the request fails
        ValueError
            If the job reaches a terminal status other than COMPLETE

        Returns
        -------
        dict
            A dictionary containing the information about the job::

                {
                   "filesProcessed" : 1,
                   "errorCount" : 0,
                   "subscriptionName" : "CRM_Import",
                   "completed_date" : "2019-12-18T22:42:32.000Z",
                   "job_status" : "COMPLETE",
                   "job_id" : 10537,
                   "jobResultSummary" : {
                      "CUSTOMKEY" : {
                         "total" : 2,
                         "recordsUpdated" : 0,
                         "recordsSkipped" : 2,
                         "newRecordsAdded" : 0,
                         "recordsInvalidated" : 0,
                         "recordsMerged" : 0
                      },
                      "HCP" : {
                         "total" : 1,
                         "recordsUpdated" : 0,
                         "recordsSkipped" : 1,
                         "recordsMerged" : 0,
                         "recordsInvalidated" : 0,
                         "newRecordsAdded" : 0
                      },
                      "ADDRESS" : {
                         "total" : 1,
                         "recordsUpdated" : 0,
                         "recordsSkipped" : 1,
                         "recordsInvalidated" : 0,
                         "newRecordsAdded" : 0,
                         "recordsMerged" : 0
                      }
                   },
                   "durationInMilliseconds" : 3000,
                   "created_date" : "2019-12-18T22:42:29.000Z",
                   "subscriptionId" : 117,
                   "processedDataSummary" : {
                      "HCP" : 1,
                      "ADDRESS" : 1
                   },
                   "type" : "MANUAL",
                   "dataLoadSummary" : {
                      "ADDRESS" : {
                         "rowsRead" : 1,
                         "rowsParsed" : 1
                      },
                      "HCP" : {
                         "rowsParsed" : 1,
                         "rowsRead" : 1
                      }
                   },
                   "badRecordCount" : 0,
                   "recordCount" : 2,
                   "matchSummary" : {
                      "HCP" : {
                         "ACT" : 1,
                         "notMatched" : 0,
                         "ASK" : 0
                      },
                      "HCO" : {
                         "ACT" : 0,
                         "notMatched" : 0,
                         "ASK" : 0
                      }
                   },
                   "responseStatus" : "SUCCESS"
                }

        """
        return self._retrieve_network_process_job(job_resp_id=job_resp_id)


class VeevaTargetSubscriptionClient(VeevaSourceSubscriptionClient):

    def __init__(
        self, dns, username, password, subscription_name, system_name, version=DEFAULT_VERSION
    ):
        """
        Create a client that enables you to manage target subscriptions that import and export data
        to and from the Veeva Network.

        Parameters
        ----------
        dns : str
            is the URL for your API service
        username : str
            the user ID for Network; for example, john.smith@veevanetwork.com.
        password : str
            the password for the user ID.
        system_name : str
            is the unique name of the system
        subscription_name : str
            is the unique name of the subscription
        version : str
            is the API version

        Raises
        ------
        HTTPError
            If the request fails
        ValueError
            If the authorization header is not available

        """
        super().__init__(dns, username, password, subscription_name, system_name, version)
        self.subscription_type = VeevaNetworkSubscriptionType.TARGET.value

    def retrieve_network_process_job(self, job_resp_id):
        """
        Retrieve the status of a source or target subscription job. This function will poll
        until the job has reached a terminal state.

        Parameters
        ----------
        job_resp_id : str
            is the unique ID of the job you want to retrieve status on

        Returns
        -------
        dict
            A dictionary containing the information about the job. A dictionary similar to the
            following is returned::

                {
                  "responseStatus": "SUCCESS",
                  "subscriptionId": 15,
                  "subscriptionName": "targetSubscriptionCustomer",
                  "durationInMilliseconds": 2000,
                  "type": "MANUAL",
                  "errorCount": 0,
                  "badRecordCount": 0,
                  "exportReferenceCount": 0,
                  "exportFull": True,
                  "exportIncludeReference": False,
                  "exportUpdatedChildOnly": False,
                  "exportSetSubscriptionStateOnFull": False,
                  "exportFormat": "CSV",
                  "exportReferenceVersion": "4",
                  "exportActiveOnly": False,
                  "jobExportCount": {
                    "LICENSE": 3961,
                    "RELATION": 333,
                    "HCO": 819,
                    "HCP": 1060,
                    "ADDRESS": 1801,
                    "EXTERNALKEYS": 8038
                  },
                  "job_id": 10563,
                  "job_status": "COMPLETE",
                  "created_date": "2016-11-17T10:58:49.000-08:00",
                  "data_revision_first": "0",
                  "data_revision_last": "929335226137870335",
                  "export_package_path": "export/change_request/targetSubscriptionCustomer/exp_000001C5.zip",
                  "total_records_exported": "1879",
                  "completed_date": "2016-11-17T10:58:51.000-08:00",
                  "export_archive": "individual",
                  "exportFormatDelimiter":"|",
                  "exportFormatTextQualifier":"\""
                }

        Raises
        ------
        HTTPError
            If the request fails
        ValueError
            If the job reaches a terminal status other than COMPLETE

        """
        return self._retrieve_network_process_job(job_resp_id=job_resp_id)
