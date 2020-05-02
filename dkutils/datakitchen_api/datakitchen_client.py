import requests

from requests.exceptions import HTTPError

from .endpoints import (
    create_order,
    get_order_runs,
)
from dkutils.constants import (KITCHEN, RECIPE, VARIATION, DEFAULT_DATAKITCHEN_URL)


class DataKitchenClient:

    def __init__(
        self,
        username,
        password,
        base_url=None,
        token=None,
        kitchen=None,
        recipe=None,
        variation=None
    ):
        """
        Client object for invoking DataKitchen API calls.

        Parameters
        ----------
        username : str
          Number of seconds to sleep in between loop executions.
        password : str
          Max duration in seconds after which the loop will exit.
        base_url: str, optional
            Base DataKitchen Platform URL
        token : str, optional
            API token
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
        self._token = token
        self._set_headers()
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

    @property
    def recipe(self):
        return self._recipe

    @recipe.setter
    def recipe(self, recipe):
        self._recipe = recipe

    @property
    def variation(self):
        return self._variation

    @variation.setter
    def variation(self, variation):
        self._variation = variation

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
        Create a new order.

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
        return create_order(
            self._headers,
            self.kitchen,
            self.recipe,
            self.variation,
            parameters=parameters,
            datakitchen_url=self._base_url
        )

    def get_order_runs(self, order_id):
        """
        Retrieve all the order runs associated with the provided order.

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
        return get_order_runs(self._headers, self.kitchen, order_id, datakitchen_url=self._base_url)
