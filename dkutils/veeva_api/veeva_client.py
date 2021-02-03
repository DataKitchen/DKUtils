import logging
import time

import requests

LOGGER = logging.getLogger()


class VeevaClient:
    def __init__(self, dns, username, password, system_name, subscription_type, subscription_name, version='v16.0'):
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
        response = requests.post(
            f'{self.base_url}systems/{self.system_name}/{self.subscription_type}_subscriptions/'
            f'{self.subscription_name}/job')
        response.raise_for_status()
        return response.json().get('job_id')

    def retrieve_network_process_job(self, job_resp_id):
        # Retrieve the extract
        retrieve_network_process_job = requests.get(
            self.base_url + 'systems/{system_name}/{subscription_type}_subscriptions/{subscript_name}/job/{job_id}'.format(
                system_name=self.system_name,
                subscription_type=self.subscription_type,
                subscript_name=self.subscription_name,
                job_id=job_resp_id),
            headers=self.admin_header)

        LOGGER.info(retrieve_network_process_job.json())
        # print(retrieve_network_process_job.json())

        if retrieve_network_process_job.json().get('job_status') == 'SUSPENDED':
            LOGGER.info("VEEVA NETWORK: The job is suspended.  Reach out to Afore to have them check it.")
            raise ValueError("The job is suspended.  Reach out to Afore to have them check it.")

        while retrieve_network_process_job.json().get('job_status') != 'COMPLETE':
            time.sleep(5.0)
            retrieve_network_process_job = requests.get(
                self.base_url + 'systems/{system_name}/{subscription_type}_subscriptions/{subscript_name}/job/{job_id}'.format(
                    system_name=self.system_name,
                    subscription_type=self.subscription_type,
                    subscript_name=self.subscription_name,
                    job_id=job_resp_id),
                headers=self.admin_header)
            # print(retrieve_network_process_job.json().get('job_status'))

            LOGGER.info(retrieve_network_process_job.json())
            # print(retrieve_network_process_job.json())

        if self.subscription_type == 'source':
            # Set some error results
            return {'source_subscription_errorcount': str(retrieve_network_process_job.json().get('errorCount')),
                    'source_subscription_recordcount': str(retrieve_network_process_job.json().get('recordCount')),
                    'source_subscription_badrecordcount': str(retrieve_network_process_job.json().get('badRecordCount'))
                    }

        elif self.subscription_type == 'target':
            return {
                'target_subscription_ADDRESS_count': str(
                    retrieve_network_process_job.json().get('jobExportCount')['ADDRESS']),
                'target_subscription_CUSTOMKEY_count': str(
                    retrieve_network_process_job.json().get('jobExportCount')['CUSTOMKEY']),
                'target_subscription_HCO_count': str(retrieve_network_process_job.json().get('jobExportCount')['HCO']),
                'target_subscription_HCP_count': str(retrieve_network_process_job.json().get('jobExportCount')['HCP']),
                'target_subscription_LICENSE_count': str(
                    retrieve_network_process_job.json().get('jobExportCount')['LICENSE']),
                'target_subscription_PARENTHCO_count': str(
                    retrieve_network_process_job.json().get('jobExportCount')['PARENTHCO']),
                'target_subscription_badrecordcount': str(retrieve_network_process_job.json().get('badRecordCount'))

            }

        else:
            return None
