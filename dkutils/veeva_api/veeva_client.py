import logging
import time

import requests

LOGGER = logging.getLogger()

TERMINAL_STATES = {"CANCELED", "COMPLETE", "FAILED", "INTERRUPTED", "KILLED", "PARKED", "PAUSED", "SUSPENDED"}


class VeevaClient:
    def __init__(self, dns, username, password, system_name, subscription_type, subscription_name, version='v16.0'):
        """
        Create a client for accessing Veeva Network

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
        subscription_type: str
            either source or target
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
        self.base_url = f'https://{dns}/api/{version}/'
        self.system_name = system_name
        self.subscription_type = subscription_type
        self.subscription_name = subscription_name

        LOGGER.info(f'VEEVA NETWORK: Attempting Authenticating')
        response = requests.post(self.base_url + 'auth', data={'username': username, 'password': password})
        response.raise_for_status()

        # The headers are then passed through as a request authorization header
        self.admin_header = {'Authorization': response.json().get('sessionId'),
                             'Content-type': 'application/json',
                             'Accept': 'application/json'}

        if self.admin_header['Authorization'] is None:
            msg = 'Could not get an authorization header'
            LOGGER.error(msg)
            raise ValueError(msg)
        else:
            LOGGER.info(f'VEEVA NETWORK: Authentication Successful!')

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
                time.sleep(5.0)
            else:
                if job_status == 'SUSPENDED':
                    LOGGER.info("VEEVA NETWORK: The job is suspended.  Reach out to Afore to have them check it.")
                    raise ValueError("The job is suspended.  Reach out to Afore to have them check it.")
                if job_status == 'COMPLETE':
                    break
                raise ValueError(f'The job has terminated with an unexpected status: {job_status}')

        if self.subscription_type == 'source':
            # Set some error results
            return {'source_subscription_errorcount': str(response.json().get('errorCount')),
                    'source_subscription_recordcount': str(response.json().get('recordCount')),
                    'source_subscription_badrecordcount': str(response.json().get('badRecordCount'))
                    }

        elif self.subscription_type == 'target':
            return {
                'target_subscription_ADDRESS_count': str(
                    response.json().get('jobExportCount')['ADDRESS']),
                'target_subscription_CUSTOMKEY_count': str(
                    response.json().get('jobExportCount')['CUSTOMKEY']),
                'target_subscription_HCO_count': str(response.json().get('jobExportCount')['HCO']),
                'target_subscription_HCP_count': str(response.json().get('jobExportCount')['HCP']),
                'target_subscription_LICENSE_count': str(
                    response.json().get('jobExportCount')['LICENSE']),
                'target_subscription_PARENTHCO_count': str(
                    response.json().get('jobExportCount')['PARENTHCO']),
                'target_subscription_badrecordcount': str(response.json().get('badRecordCount'))

            }

        else:
            return None
