import logging
import time

import requests

LOGGER = logging.getLogger()

TERMINAL_STATES = {"CANCELED", "COMPLETE", "FAILED", "INTERRUPTED", "KILLED", "PARKED", "PAUSED", "SUSPENDED"}

DEFAULT_VERSION = "v16.0"


def _raise_exception(msg):
    LOGGER.error(msg)
    raise ValueError(msg)


class VeevaNetworkClient:
    def __init__(self, dns, username, password, version):
        """
        Create a client for accessing Veeva Network. This class should not be instantiated directly. You should use
        either VeevaSourceSubscriptionClient or VeevaTargetSubscriptionClient

        Parameters
        ----------
        dns: str
            is the URL for your API service
        username
            the user ID for Network; for example, john.smith@veevanetwork.com.
        password: str
            the password for the user ID.
        version: str
            is the API version

        Raises
        ------
        HTTPError
            If the request fails

        ValueError
            If the authorization header is not available
        """
        self.base_url = f'https://{dns}/api/{version if version else "v16.0"}/'

        LOGGER.info(f'VEEVA NETWORK: Attempting Authenticating')
        response = requests.post(self.base_url + 'auth', data={'username': username, 'password': password})
        response.raise_for_status()

        # The headers are then passed through as a request authorization header
        self.admin_header = {'Authorization': response.json().get('sessionId'),
                             'Content-type': 'application/json',
                             'Accept': 'application/json'}

        if self.admin_header['Authorization'] is None:
            _raise_exception('Could not get an authorization header')
        else:
            LOGGER.info(f'VEEVA NETWORK: Authentication Successful!')


class VeevaSourceSubscriptionClient(VeevaNetworkClient):

    def __init__(self, dns, username, password, subscription_name, system_name, version=DEFAULT_VERSION):
        """
        Create a client that enables you to manage source subscriptions that import and export data to
        and from the Veeva Network.

        Parameters
        ----------
        dns: str
            is the URL for your API service
        username
            the user ID for Network; for example, john.smith@veevanetwork.com.
        password: str
            the password for the user ID.
        system_name: str
            is the unique name of the system
        subscription_name: str
            is the unique name of the subscription
        version: str
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
        self.subscription_type = 'source'
        super().__init__(dns, username, password, version)

    def run_subscription_process(self):
        """
        This API enables you to create a source or target subscription job.
        Note: This API requires system administrator or API-only permissions.

        Returns
        -------
        str
            the unique ID of the job generated for the source subscription you specified.

         Raises
        ------
        HTTPError
            If the request fails
        """
        response = requests.post(
            f'{self.base_url}systems/{self.system_name}/{self.subscription_type}_subscriptions/'
            f'{self.subscription_name}/job')
        response.raise_for_status()
        return response.json().get('job_id')

    def _retrieve_network_process_job(self, job_resp_id, sleep_seconds=5):
        """
        Retrieve the status of a source or target subscription job. This function will poll
        until the job has reached a terminal state.
        Parameters
        ----------
        job_resp_id: str
            is the unique ID of the job you want to retrieve status on
        sleep_seconds: float, optional
            sleep the given number of seconds betweening polling for the job status.  The argument may be
            a floating point number for subsecond precision.
        Returns
        -------
        dict
            A dictionary containing the information about the job. For a source job a dictionary similar to the
            following is returned:
            {'source_subscription_errorcount': 0,
             'source_subscription_recordcount': 0,
             'source_subscription_badrecordcount': 0
            }
            For a target job a dictionary similar to the following is returned:
            {
                'target_subscription_ADDRESS_count': "123 anywhere",
                'target_subscription_CUSTOMKEY_count': "whatever",
                'target_subscription_HCO_count': 0,
                'target_subscription_HCP_count': 0,
                'target_subscription_LICENSE_count': "123abc",
                'target_subscription_PARENTHCO_count': "something",
                'target_subscription_badrecordcount': 0

            }
        Raises
        ------
        HTTPError
            If the request fails

        ValueError
            If the job reaches a terminal status other than COMPLETE
        """
        while True:
            response = requests.get(
                f'{self.base_url}systems/{self.system_name}/{self.subscription_type}_subscriptions/'
                f'{self.subscription_name}/job/{job_resp_id}',
                headers=self.admin_header)
            response.raise_for_status()
            job_status = response.json().get('job_status')
            if job_status not in TERMINAL_STATES:
                LOGGER.info(job_status)
                time.sleep(sleep_seconds)
            else:
                if job_status == 'SUSPENDED':
                    _raise_exception("VEEVA NETWORK: The job is scheduled and is waiting for shared resources prior to "
                                     "becoming active.")
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
        job_resp_id: str
            is the unique ID of the job you want to retrieve status on

        Returns
        -------
        dict
            A dictionary containing the information about the job.
            {'source_subscription_errorcount': 0,
             'source_subscription_recordcount': 0,
             'source_subscription_badrecordcount': 0
            }

        Raises
        ------
        HTTPError
            If the request fails

        ValueError
            If the job reaches a terminal status other than COMPLETE
        """
        json = self._retrieve_network_process_job(job_resp_id=job_resp_id)

        return {'source_subscription_errorcount': str(json.get('errorCount')),
                'source_subscription_recordcount': str(json.get('recordCount')),
                'source_subscription_badrecordcount': str(json.get('badRecordCount'))
                }


class VeevaTargetSubscriptionClient(VeevaSourceSubscriptionClient):

    def __init__(self, dns, username, password, subscription_name, system_name, version=DEFAULT_VERSION):
        """
        Create a client that enables you to manage target subscriptions that import and export data to
        and from the Veeva Network.

        Parameters
        ----------
        dns: str
            is the URL for your API service
        username
            the user ID for Network; for example, john.smith@veevanetwork.com.
        password: str
            the password for the user ID.
        system_name: str
            is the unique name of the system
        subscription_name: str
            is the unique name of the subscription
        version: str
            is the API version

        Raises
        ------
        HTTPError
            If the request fails

        ValueError
            If the authorization header is not available
        """
        super().__init__(dns, username, password, subscription_name, system_name, version)
        self.subscription_type = 'target'

    def retrieve_network_process_job(self, job_resp_id):
        """
        Retrieve the status of a source or target subscription job. This function will poll
        until the job has reached a terminal state.
        Parameters
        ----------
        job_resp_id: str
            is the unique ID of the job you want to retrieve status on

        Returns
        -------
        dict
            A dictionary containing the information about the job. A dictionary similar to the following is returned:
            {
                'target_subscription_ADDRESS_count': "123 anywhere",
                'target_subscription_CUSTOMKEY_count': "whatever",
                'target_subscription_HCO_count': 0,
                'target_subscription_HCP_count': 0,
                'target_subscription_LICENSE_count': "123abc",
                'target_subscription_PARENTHCO_count': "something",
                'target_subscription_badrecordcount': 0

            }
        Raises
        ------
        HTTPError
            If the request fails

        ValueError
            If the job reaches a terminal status other than COMPLETE
        """
        json = self._retrieve_network_process_job(job_resp_id=job_resp_id)

        return {
            'target_subscription_ADDRESS_count': str(
                json.get('jobExportCount')['ADDRESS']),
            'target_subscription_CUSTOMKEY_count': str(
                json.get('jobExportCount')['CUSTOMKEY']),
            'target_subscription_HCO_count': str(json.get('jobExportCount')['HCO']),
            'target_subscription_HCP_count': str(json.get('jobExportCount')['HCP']),
            'target_subscription_LICENSE_count': str(
                json.get('jobExportCount')['LICENSE']),
            'target_subscription_PARENTHCO_count': str(
                json.get('jobExportCount')['PARENTHCO']),
            'target_subscription_badrecordcount': str(json.get('badRecordCount'))

        }
