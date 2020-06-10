import copy
import requests
import traceback

from requests.exceptions import HTTPError

from dkutils.constants import (
    API_GET,
    API_POST,
    API_PUT,
    DEFAULT_DATAKITCHEN_URL,
    DEFAULT_VAULT_URL,
    KITCHEN,
    ORDER_ID,
    ORDER_RUN_ID,
    ORDER_RUN_STATUS,
    RECIPE_OVERRIDES,
    PARAMETERS,
    PARENT_KITCHEN,
    RECIPE,
    STOPPED_STATUS_TYPES,
    VARIATION,
)
from dkutils.validation import get_max_concurrency, skip_token_validation
from dkutils.wait_loop import WaitLoop
from dkutils.dictionary_comparator import DictionaryComparator
from .datetime_utils import get_utc_timestamp

# The servings API endpoint retrieves only 10 order runs by default. To retrieve them all, assume
# 100K exceeds the max order runs a given order will ever contain.
DEFAULT_SERVINGS_COUNT = 100000


def _ensure_and_get_kitchen(kitchen, kitchens):
    if kitchen not in kitchens:
        raise ValueError(f'No kitchen with the name: {kitchen} was found in the available kitchens')
    return kitchens[kitchen]


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

    def _api_request(self, http_method, *args, is_json=True, **kwargs):
        """
        Make HTTP request to arbitrary API endpoint, with optional parameters as payload.

        Parameters
        ----------
        http_method : str
            HTTP method to use when making API request.
        *args : list
            Variable length list of strings to construct endpoint path.
        is_json : bool
            Set to False if payload/response is not JSON data.
        **kwargs : dict
            Arbitrary keyword arguments to construct request payload.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object
        """
        if not skip_token_validation():
            self._refresh_token()
        api_request = getattr(requests, http_method)
        api_path = f'{self._base_url}/v2/{"/".join(args)}'
        if is_json:
            response = api_request(api_path, headers=self._headers, json=kwargs)
        else:
            response = api_request(api_path, headers=self._headers, data=kwargs)
        response.raise_for_status()
        return response

    def _validate_token(self):
        """
        Validate the current token.

        Returns
        -------
        boolean
            True if the current token is valid, False otherwise
        """
        try:
            self._api_request(API_GET, 'validatetoken')
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

        self._token = self._api_request(
            API_POST, 'login', is_json=False, username=self._username, password=self._password
        ).text
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
        return self._api_request(
            API_PUT,
            'order',
            'create',
            self.kitchen,
            self.recipe,
            self.variation,
            schedule='now',
            parameters=parameters
        )

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
        return self._api_request(
            API_PUT, 'order', 'resume', order_run_id, kitchen_name=self.kitchen
        )

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
        try:
            api_response = self._api_request(
                API_GET, 'order', 'servings', self.kitchen, order_id, count=DEFAULT_SERVINGS_COUNT
            ).json()
            return api_response['servings']
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
        api_response = self._api_request(
            API_POST,
            'order',
            'details',
            self.kitchen,
            logs=False,
            serving_hid=str(order_run_id),
            servingjson=False,
            summary=False,
            testresults=False,
            timingresults=False
        ).json()
        return api_response['servings'][0]

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

    def create_and_monitor_orders(
        self, orders_details, sleep_secs, duration_secs, max_concurrent=None
    ):
        """
        Create the specified orders and wait for them to complete (or timeout after the specified
        duration_secs).

        Parameters
        ----------
        orders_details : list
            List of order_details, each of which contains the kitchen, recipe, and variation of
            the order to create, as well as an optional dictionary of parameters. An example
            order_details item is of the form::

                {
                    "kitchen": "IM_Development",
                    "recipe": "Demo_Recipe_Replay",
                    "variation": "Process_Daily_Data",
                    "parameters": {
                        "DT": "20200529"
                    }
                }

        sleep_secs : int
            Number of seconds to sleep in between loop executions.
        duration_secs : int
            Max duration in seconds after which the loop will exit.
        max_concurrent : integer or None
            Max number of orders to kick off concurrently. If None, all orders will be kicked off
            concurrently.

        Returns
        -------
        list
            List of 3 lists: [completed orders, active orders, queued orders]. If all the
            orders completed in the provided duration_secs, then active orders and queued orders
            will be empty lists. The completed orders and active orders lists contain the
            orders_details entries with order_id, order_run_id, and order_status fields appended to
            each entry. These additional fields will all be populated in the completed orders list.
            However, the order_run_id and order_run_status fields may be None if the timeout
            occurred before the order run id for the created order was obtained. The final queued
            orders list contains a copy of the order_details entries that never made it out of the
            queue, with no additional fields added. An example order_details entry for the
            completed orders and active orders array will be of the form::

                {
                    "kitchen": "IM_Development",
                    "recipe": "Demo_Recipe_Replay",
                    "variation": "Process_Daily_Data",
                    "parameters": {
                        "DT": "20200529"
                    }
                    "order_id": "dc90de6e-a12b-11ea-8ba5-96323db651da",
                    "order_run_id": "f9b107a8-a12b-11ea-a95a-72553da658b3",
                    "order_run_status": "COMPLETED_SERVING",
                }

        """
        # Orders will be popped of this queue, so create a copy of orders_details in reverse order
        queued_orders = [copy.deepcopy(od) for od in orders_details[::-1]]

        # Ensure max concurrent variable is valid
        num_total_orders = len(queued_orders)
        max_concurrent = get_max_concurrency(num_total_orders, max_concurrent)

        def create_order(order_details):
            self.kitchen = order_details[KITCHEN]
            self.recipe = order_details[RECIPE]
            self.variation = order_details[VARIATION]
            parameters = order_details[PARAMETERS] if PARAMETERS in order_details else {}
            order_details[ORDER_ID] = self.create_order(parameters=parameters).json()[ORDER_ID]
            order_details[ORDER_RUN_ID] = None
            order_details[ORDER_RUN_STATUS] = None
            return order_details

        # Create initial orders
        active_orders = [create_order(queued_orders.pop()) for _ in range(max_concurrent)]
        completed_orders = []

        wait_loop = WaitLoop(sleep_secs, duration_secs)
        while wait_loop:
            cur_completed_orders = []
            for active_order in active_orders:
                self.kitchen = active_order[KITCHEN]
                if active_order[ORDER_RUN_ID] is not None:
                    active_order[ORDER_RUN_STATUS] = self.get_order_run_status(
                        active_order[ORDER_RUN_ID]
                    )
                    if active_order[ORDER_RUN_STATUS] in STOPPED_STATUS_TYPES:
                        completed_orders.append(active_order)
                        cur_completed_orders.append(active_order)
                else:
                    order_runs = self.get_order_runs(active_order[ORDER_ID])
                    if order_runs:
                        active_order[ORDER_RUN_ID] = order_runs[0]['hid']

            for completed_order in cur_completed_orders:
                active_orders.remove(completed_order)
                if len(queued_orders) > 0:
                    active_orders.append(create_order(queued_orders.pop()))

            if len(active_orders) == 0:
                break

        return completed_orders, active_orders, queued_orders

    def resume_and_monitor_orders(
        self, order_runs_details, sleep_secs, duration_secs, max_concurrent=None
    ):
        """
        Resume the specified order runs and wait for them to complete (or timeout after the
        specified duration_secs).

        Parameters
        ----------
        order_runs_details : list
            List of order_runs_details, each of which contains the kitchen and order run id. An
            example order_run_details item is of the form::

                {
                    "kitchen": "IM_Development",
                    "order_run_id": "84e77b50-a1f3-11ea-aaaf-521d4744de4c"
                }
        sleep_secs : int
            Number of seconds to sleep in between loop executions.
        duration_secs : int
            Max duration in seconds after which the loop will exit.
        max_concurrent : integer or None
            Max number of orders to kick off concurrently. If None, all orders will be kicked off
            concurrently.

        Returns
        -------
        list
            List of 3 lists: [completed orders, active orders, queued orders]. If all the
            orders completed in the provided duration_secs, then active orders and queued orders
            will be empty lists. The completed orders and active orders lists contain the
            orders_details entries with order_id, order_run_id, and order_status fields appended to
            each entry. These additional fields will all be populated in the completed orders list.
            However, the order_run_id and order_run_status fields may be None if the timeout
            occurred before the order run id for the created order was obtained. The final queued
            orders list contains a copy of the order_details entries that never made it out of the
            queue, with no additional fields added. An example order_details entry for the
            completed orders and active orders array will be of the form::

                {
                    "kitchen": "IM_Development",
                    "order_id": "dc90de6e-a12b-11ea-8ba5-96323db651da",
                    "order_run_id": "f9b107a8-a12b-11ea-a95a-72553da658b3",
                    "order_run_status": "COMPLETED_SERVING",
                }

        """
        # Order runs will be popped of this queue, so create a copy of order_runs_details in
        # reverse order
        queued_orders = [copy.deepcopy(od) for od in order_runs_details[::-1]]

        # Ensure max concurrent variable is valid
        num_total_orders = len(queued_orders)
        max_concurrent = get_max_concurrency(num_total_orders, max_concurrent)

        def resume_order(order_run_details):
            self.kitchen = order_run_details[KITCHEN]
            order_run_details[ORDER_ID] = self.resume_order_run(order_run_details[ORDER_RUN_ID]
                                                                ).json()[ORDER_ID]
            order_run_details[ORDER_RUN_ID] = None
            order_run_details[ORDER_RUN_STATUS] = None
            return order_run_details

        # Used to differentiate the resumed order runs from the order runs they were resumed from
        resume_start_time = get_utc_timestamp()

        # Create initial orders
        active_orders = [resume_order(queued_orders.pop()) for _ in range(max_concurrent)]
        completed_orders = []

        wait_loop = WaitLoop(sleep_secs, duration_secs)
        while wait_loop:
            cur_completed_orders = []
            for active_order in active_orders:
                self.kitchen = active_order[KITCHEN]
                if active_order[ORDER_RUN_ID] is not None:
                    active_order[ORDER_RUN_STATUS] = self.get_order_run_status(
                        active_order[ORDER_RUN_ID]
                    )
                    if active_order[ORDER_RUN_STATUS] in STOPPED_STATUS_TYPES:
                        completed_orders.append(active_order)
                        cur_completed_orders.append(active_order)
                else:
                    order_runs = self.get_order_runs(active_order[ORDER_ID])

                    # Ensure the latest order run is the resumed one and not the run from which it
                    # was resumed.
                    if order_runs[0]['timings']['start-time'] > resume_start_time:
                        active_order[ORDER_RUN_ID] = order_runs[0]['hid']

            for completed_order in cur_completed_orders:
                active_orders.remove(completed_order)
                if len(queued_orders) > 0:
                    active_orders.append(resume_order(queued_orders.pop()))

            if len(active_orders) == 0:
                break

        return completed_orders, active_orders, queued_orders

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
        return self._api_request(API_POST, 'vault', 'config', **payload)

    def _get_kitchens_info(self):
        """
        Get information about available kitchens

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        -------
        dict
            A dictionary keyed by kitchen name containing information about each kitchen.
            For example:
                {"test_kitchen": {
                    '_created': None,
                    '_finished': False,
                    'created_time': 1582037782076,
                    'creator_user': 'ddicara+im@datakitchen.io',
                    'customer': 'Implementation',
                    'description': 'Implementation Customer development environment.',
                    'git_name': 'im',
                    'git_org': 'DKImplementation',
                    'kitchen-staff': ['aarthy+im@datakitchen.io'],
                    'mesos-constraint': True,
                    'mesos-group': 'implementation_dev',
                    'name': 'IM_Development',
                    'parent-kitchen': 'IM_Production',
                    'recipeoverrides': {'DKUtilsVersion': '0.5.0'},
                    'recipes': ['Utility_Wizard_Ingredients'],
                    'restrict-recipes': False,
                    'settings': {
                        'agile-tools': None,
                        'alerts': {
                            'orderrunError': None, 'orderrunOverDuration': None,
                            'orderrunStart': None, 'orderrunSuccess': None},
                        'backup': {
                            'backup_enabled': False, 'backup_failure_email': None,
                            'backup_success_email': None, 'export_key_timing': False,
                            'export_node_timing': False, 'export_test_data': False,
                            'last_backup': None, 's3_access_key': None, 's3_bucket': None,
                            's3_secret_key': None, 'target_folder': None}},
                    'wizard-status': {}
                }}

        """
        kitchens = {}
        for kitchen in self._api_request(API_GET, 'kitchen', 'list').json()['kitchens']:
            name = kitchen['name']
            if name in kitchens:
                raise ValueError(
                    f'More than 1 kitchen with the name: {name} found in list of kitchens'
                )
            kitchens[name] = kitchen
        return kitchens

    def _get_kitchen_info(self):
        """
        Gets information about the current kitchen

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the kitchen attribute is not set
            if more than one entry is found with the kitchen name

        Returns
        -------
        dict
            A dictionary containing information specific to the current kitchen in the form:
                {
                    '_created': None,
                    '_finished': False,
                    'created_time': 1582037782076,
                    'creator_user': 'ddicara+im@datakitchen.io',
                    'customer': 'Implementation',
                    'description': 'Implementation Customer development environment.',
                    'git_name': 'im',
                    'git_org': 'DKImplementation',
                    'kitchen-staff': ['aarthy+im@datakitchen.io'],
                    'mesos-constraint': True,
                    'mesos-group': 'implementation_dev',
                    'name': 'IM_Development',
                    'parent-kitchen': 'IM_Production',
                    'recipeoverrides': {'DKUtilsVersion': '0.5.0'},
                    'recipes': ['Utility_Wizard_Ingredients'],
                    'restrict-recipes': False,
                    'settings': {
                        'agile-tools': None,
                        'alerts': {
                            'orderrunError': None, 'orderrunOverDuration': None,
                            'orderrunStart': None, 'orderrunSuccess': None},
                        'backup': {
                            'backup_enabled': False, 'backup_failure_email': None,
                            'backup_success_email': None, 'export_key_timing': False,
                            'export_node_timing': False, 'export_test_data': False,
                            'last_backup': None, 's3_access_key': None, 's3_bucket': None,
                            's3_secret_key': None, 'target_folder': None}},
                    'wizard-status': {}
                }

        """
        self._ensure_attributes(KITCHEN)
        kitchens = self._get_kitchens_info()
        return _ensure_and_get_kitchen(self.kitchen, kitchens)

    def _update_kitchen(self, kitchen_info):
        """
                Updates information about the current kitchen

                Parameters
                ----------
                kitchen_info : dict
                    A dictionary containing information about the current kitchen in the form:
                        {
                            '_created': None,
                            '_finished': False,
                            'created_time': 1582037782076,
                            'creator_user': 'ddicara+im@datakitchen.io',
                            'customer': 'Implementation',
                            'description': 'Implementation Customer development environment.',
                            'git_name': 'im',
                            'git_org': 'DKImplementation',
                            'kitchen-staff': ['aarthy+im@datakitchen.io'],
                            'mesos-constraint': True,
                            'mesos-group': 'implementation_dev',
                            'name': 'IM_Development',
                            'parent-kitchen': 'IM_Production',
                            'recipeoverrides': {'DKUtilsVersion': '0.5.0'},
                            'recipes': ['Utility_Wizard_Ingredients'],
                            'restrict-recipes': False,
                            'settings': {
                                'agile-tools': None,
                                'alerts': {
                                    'orderrunError': None, 'orderrunOverDuration': None,
                                    'orderrunStart': None, 'orderrunSuccess': None},
                                'backup': {
                                    'backup_enabled': False, 'backup_failure_email': None,
                                    'backup_success_email': None, 'export_key_timing': False,
                                    'export_node_timing': False, 'export_test_data': False,
                                    'last_backup': None, 's3_access_key': None, 's3_bucket': None,
                                    's3_secret_key': None, 'target_folder': None}},
                            'wizard-status': {}
                        }
                Raises
                ------
                HTTPError
                    If the request fails.
                ValueError
                    If the kitchen attribute is not set
                    If the name in the given kitchen_info does not match that of the current kitchen

                """
        self._ensure_attributes(KITCHEN)
        if kitchen_info['name'] != self.kitchen:
            raise (
                ValueError(
                    f'Name in kitchen_info: {kitchen_info["name"]} does not match current kitchen: {self.kitchen}'
                )
            )
        payload = {"kitchen.json": kitchen_info}
        self._api_request(API_POST, 'kitchen', 'update', self.kitchen, **payload)

    def get_overrides(self):
        """
        Returns a dictionary containing the overrides for the current kitchen

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the kitchen attribute is not set
            If the name in the given kitchen_info does not match that of the current kitchen

        Returns
        -------
        dict
            A dictionary containing the overides

        """
        return self._get_kitchen_info()[RECIPE_OVERRIDES]

    def update_overrides(self, overrides):
        """
        Updates the overrides for the current kitchen

        Parameters
        ----------
        dict
            A dictionary containing the overrides

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the kitchen attribute is not set
            If the name in the given kitchen_info does not match that of the current kitchen
        """
        kitchen_info = self._get_kitchen_info()
        kitchen_info[RECIPE_OVERRIDES] = overrides
        self._update_kitchen(kitchen_info)

    def compare_overrides(self, other=None):
        """
        Compare the overrides in the current kitchen to those of the specified kitchen. If other is None then
        the comparison is done against the parent kitchen

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the kitchen attribute is not set
            If the name of the specified kitchen doesn't match any available kitchen

        Returns
        _______
        DictionaryComparator
            A DictionaryCompparator which can be used to get the results of the comparison
        """
        self._ensure_attributes(KITCHEN)
        kitchens = self._get_kitchens_info()
        my_kitchen_info = _ensure_and_get_kitchen(self.kitchen, kitchens)
        if not other:
            other = my_kitchen_info[PARENT_KITCHEN]
        _ensure_and_get_kitchen(other, kitchens)
        my_overrides = my_kitchen_info[RECIPE_OVERRIDES]
        other_overrides = kitchens[other][RECIPE_OVERRIDES]
        return DictionaryComparator(my_overrides, other_overrides)
