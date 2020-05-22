import requests
import traceback

from requests.exceptions import HTTPError

from dkutils.constants import (
    KITCHEN, RECIPE, VARIATION, DEFAULT_DATAKITCHEN_URL, DEFAULT_VAULT_URL, STOPPED_STATUS_TYPES
)
from dkutils.wait_loop import WaitLoop

# The servings API endpoint retrieves only 10 order runs by default. To retrieve them all, assume
# 100K exceeds the max order runs a given order will ever contain.
DEFAULT_SERVINGS_COUNT = 100000


class DataKitchenClient:

    def __init__(
        self, username, password, base_url=None, kitchen=None, recipe=None, variation=None
    ):
        """
        Client object for invoking DataKitchen API calls. If the API call requires a kitchen,
        recipe, and/or variation, you must set those fields on the client instance prior to
        invoking those methods (or set them via the constructor when a class instance is
        created).

        Parameters
        ----------
        username : str
          Username to authenticate and obtain a session token via the DataKitchen login API.
        password : str
          Password to authenticate and obtain a session token via the DataKitchen login API.
        base_url: str, optional
            Base DataKitchen Platform URL
        kitchen : str, optional
            Kitchen to use in API requests
        recipe : str, optional
            Recipe to use in API requests
        variation : str, optional
            Variation to use in API requests
        """
        self._username = username
        self._password = password
        self._base_url = base_url if base_url else DEFAULT_DATAKITCHEN_URL
        self._token = None
        self._headers = None
        self._refresh_token()
        self.kitchen = kitchen
        self.recipe = recipe
        self.variation = variation

    @property
    def kitchen(self):
        return self._kitchen

    @kitchen.setter
    def kitchen(self, kitchen):
        self._kitchen = kitchen

    def set_kitchen(self, kitchen):
        self.kitchen = kitchen
        return self

    @property
    def recipe(self):
        return self._recipe

    @recipe.setter
    def recipe(self, recipe):
        self._recipe = recipe

    def set_recipe(self, recipe):
        self.recipe = recipe
        return self

    @property
    def variation(self):
        return self._variation

    @variation.setter
    def variation(self, variation):
        self._variation = variation

    def set_variation(self, variation):
        self.variation = variation
        return self

    def _ensure_attributes(self, *args):
        """
        Ensure the properties required for the API request are all defined.
        """
        invalid_attributes = []
        for attr_name in args:
            if getattr(self, attr_name) is None:
                invalid_attributes.append(attr_name)
        if invalid_attributes:
            raise ValueError(f'Undefined attributes: ",".join({invalid_attributes})')

    def _validate_token(self):
        """
        Validate the current token.

        Returns
        -------
        boolean
            True if the current token is valid, False otherwise
        """
        try:
            validate_token_url = f'{self._base_url}/v2/validatetoken'
            response = requests.get(validate_token_url, headers=self._headers)
            response.raise_for_status()
            return True
        except HTTPError:
            return False

    def _refresh_token(self):
        """
        Validate the existing token. If invalid, refresh the token by logging into the DataKitchen
        platform via the login API to retrieve a fresh token. Reset the current headers if the
        token is refreshed.

        Raises
        ------
        HTTPError
            If the login request fails to obtain a new token (e.g. login credentials are invalid).
        """

        if self._validate_token():
            return

        credentials = dict()
        credentials['username'] = self._username
        credentials['password'] = self._password

        login_url = f'{self._base_url}/v2/login'
        response = requests.post(login_url, data=credentials)
        response.raise_for_status()
        self._token = response.text
        self._set_headers()

    def _set_headers(self):
        """
        Set the headers dictionary with the current token.
        """
        self._headers = {'Authorization': f'Bearer {self._token}'}

    def create_order(self, parameters={}):
        """
        Create a new order. Kitchen, recipe and variation attributes must be set prior to invoking
        this method.

        Parameters
        ----------
        parameters : dict, optional
            Dictionary of variable overrides (default is empty dictionary)

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        ------
        requests.Response
            :class:`Response <Response>` object
        """
        self._ensure_attributes(KITCHEN, RECIPE, VARIATION)
        self._refresh_token()
        order_create_url = f'{self._base_url}/v2/order/create/{self.kitchen}/{self.recipe}/{self.variation}'
        payload = {"schedule": "now", "parameters": parameters}
        response = requests.put(order_create_url, headers=self._headers, json=payload)
        response.raise_for_status()
        return response

    def resume_order_run(self, order_run_id):
        """
        Resume a failed order run. Kitchen attribute must be set prior to invoking this method.

        Parameters
        ----------
        order_run_id : str
            Failed order run id to resume.

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        ------
        requests.Response
            :class:`Response <Response>` object
        """
        self._ensure_attributes(KITCHEN)
        self._refresh_token()
        order_run_resume_url = f'{self._base_url}/v2/order/resume/{order_run_id}'
        payload = {'kitchen_name': self.kitchen}
        response = requests.put(order_run_resume_url, headers=self._headers, json=payload)
        response.raise_for_status()
        return response

    def get_order_runs(self, order_id):
        """
        Retrieve all the order runs associated with the provided order. The kitchen attribute
        must be set prior to invoking this method.

        Parameters
        ----------
        order_id : str
            Order id for which to retrieve order runs

        Returns
        ------
        list or None
            None if no order runs are found. Otherwise, return a list of order run details. Each order
            run details entry is of the form::

                {
                    "order_id": "71d8a966-38e0-11ea-8cf9-a6bbea194887",
                    "status": "COMPLETED_SERVING",
                    "orderrun_status": "OrderRun Completed",
                    "hid": "a8978ddc-83c7-11ea-88ba-9a815c325cee",
                    "variation_name": "dk_agent_checker_run_hourly",
                    "timings": {
                      "start-time": 1587470413845,
                      "end-time": 1587470432441,
                      "duration": 18596
                    }
                }

        """
        self._ensure_attributes(KITCHEN)
        self._refresh_token()
        try:
            order_status_url = f'{self._base_url}/v2/order/servings/{self.kitchen}/{order_id}'
            payload = {'count': DEFAULT_SERVINGS_COUNT}
            response = requests.get(order_status_url, headers=self._headers, json=payload)
            response.raise_for_status()
            return response.json()['servings']
        except HTTPError:
            print(
                f'No order runs found for provided order id ({order_id}) in kitchen {self.kitchen}'
            )

    def get_order_run_details(self, order_run_id):
        """
        Retrieve the details of an order run.

        Parameters
        ----------
        order_run_id : str
            Order run id for which to retrieve details

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        ------
        dict
            Order run details of the form::

                {
                    "order_id": "ca789c92-8bb6-11ea-883f-46ee3c6afcbf",
                    "hid": "cd463d80-8bb6-11ea-97c5-8a10ccb96113",
                    "recipe_id": "ce7b696e-8bb6-11ea-97c5-8a10ccb96113",
                    "status": "SERVING_ERROR",
                    "variation_name": "sub_workflow",
                    "recipe_name": "Sub_Workflow",
                    "run_time_variables": {
                        "CAT": "CLS",
                        "CurrentKitchen": "Add_Real_Data_and_Infrastructure",
                        "CurrentOrderId": "ca789c92-8bb6-11ea-883f-46ee3c6afcbf",
                        "CurrentOrderRunId": "cd463d80-8bb6-11ea-97c5-8a10ccb96113",
                        "CurrentVariation": "sub_workflow",
                        "DH": "12",
                        "DT": "20200426",
                        ...
                        ...
                        ...
                        "tableauConfig": {
                            "username": "",
                            "password": "",
                            "url_login": "",
                            "url": "",
                            "selenium_url": "",
                            "content_url": ""
                        }
                    },
                    "orderrun_status": "Error in OrderRun",
                    "resumed_by": null,
                    "scheduled_start_time": 1588342778543,
                    "variation": {},
                    "state": "unknown DKNodeStatus"
                }

        """
        self._ensure_attributes(KITCHEN)
        self._refresh_token()
        order_run_details_url = f'{self._base_url}/v2/order/details/{self.kitchen}'
        payload = {
            'logs': False,
            'serving_hid': f'{order_run_id}',
            'servingjson': False,
            'summary': False,
            'testresults': False,
            'timingresults': False
        }
        response = requests.post(order_run_details_url, headers=self._headers, json=payload)
        response.raise_for_status()
        return response.json()['servings'][0]

    def get_order_run_status(self, order_run_id):
        """
        Retrieve the status of the provided order run. If the order run isn't found, return None.

        Parameters
        ----------
        order_run_id : str
            Order run for which to retrieve status

        Returns
        -------
        str or none
            One of PLANNED_SERVING, ACTIVE_SERVING, COMPLETED_SERVING, STOPPED_SERVING,
            SERVING_ERROR, SERVING_RERAN, or None if the order run is not found.
        """
        self._ensure_attributes(KITCHEN)
        self._refresh_token()
        try:
            return self.get_order_run_details(order_run_id)['status']
        except HTTPError:
            print(f'Order run retrieval failure:\n{traceback.format_exc()}')
            return None

    def monitor_order_run(self, sleep_secs, duration_secs, order_run_id):
        """
        Wait for the specified order run to complete and return completion status when finished.
        If the order run takes > duration_secs, return None.

        Parameters
        ----------
        sleep_secs : int
            Number of seconds to sleep in between loop executions.
        duration_secs : int
            Max duration in seconds after which the loop will exit.
        order_run_id : str
            Order run for which to wait until it's completed

        Returns
        -------
        str or none
            One of PLANNED_SERVING, ACTIVE_SERVING, COMPLETED_SERVING, STOPPED_SERVING,
            SERVING_ERROR, SERVING_RERAN, or None if the order run is not found.
        """
        order_run_ids = {order_run_id: self.kitchen}
        order_run_statuses = self.monitor_order_runs(sleep_secs, duration_secs, order_run_ids)
        return order_run_statuses[order_run_id]

    def monitor_order_runs(self, sleep_secs, duration_secs, order_run_ids):
        """
        Wait for the specified order runs to complete and return completion status when finished.
        If the order runs take > duration_secs, return None.

        Parameters
        ----------
        sleep_secs : int
            Number of seconds to sleep in between loop executions.
        duration_secs : int
            Max duration in seconds after which the loop will exit.
        order_run_ids : dict
            Dictionary keyed by order run id and valued by kitchen for the order runs to wait
            for completion.

        Returns
        -------
        dict or none
            Dictionary keyed by order run id and valued by one of PLANNED_SERVING, ACTIVE_SERVING,
            COMPLETED_SERVING, STOPPED_SERVING, SERVING_ERROR, SERVING_RERAN, or None if the order
            run is not found.
        """
        wait_loop = WaitLoop(sleep_secs, duration_secs)
        completed_order_runs = {}
        while wait_loop:
            for order_run_id, kitchen in order_run_ids.items():
                if order_run_id not in completed_order_runs:
                    self.kitchen = kitchen
                    order_run_status = self.get_order_run_status(order_run_id)
                    if order_run_status in STOPPED_STATUS_TYPES:
                        completed_order_runs[order_run_id] = order_run_status
                if len(order_run_ids) == len(completed_order_runs):
                    return completed_order_runs

        for order_run_id in order_run_ids.keys():
            if order_run_id not in completed_order_runs:
                completed_order_runs[order_run_id] = None
        return completed_order_runs

    def update_kitchen_vault(
        self,
        prefix,
        vault_token,
        vault_url=DEFAULT_VAULT_URL,
        private=False,
        inheritable=True,
    ):
        """
        Updates the custom vault configuration for a Kitchen.

        Parameters
        ----------
        prefix : str
            Prefix specifying the vault location (e.g. Implementation/dev).
        vault_token : str
            Token for the custom vault.
        vault_url : str, optional
            Vault URL (default: https://vault2.datakitchen.io:8200).
        private : str, optional
            Set to True if this is a private vault service, otherwise set to False (default: False)
        inheritable : str, optional
            Set to True if this vault should be inherited by child kitchens, otherwise set to false
            (default: True).

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        ------
        requests.Response
            :class:`Response <Response>` object
        """
        self._ensure_attributes(KITCHEN)
        self._refresh_token()
        vault_config_url = f'{self._base_url}/v2/vault/config'
        payload = {
            'config': {
                self.kitchen: {
                    'inheritable': inheritable,
                    'prefix': prefix,
                    'private': private,
                    'service': 'custom',
                    'token': vault_token,
                    'url': vault_url
                }
            }
        }
        response = requests.post(vault_config_url, headers=self._headers, json=payload)
        response.raise_for_status()
        return response
