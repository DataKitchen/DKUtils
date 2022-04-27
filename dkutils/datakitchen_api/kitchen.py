from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from dkutils.constants import (
    API_DELETE,
    API_GET,
    API_POST,
    API_PUT,
)

if TYPE_CHECKING:
    from .datakitchen_client import DataKitchenClient

logger = logging.getLogger(__name__)


class Kitchen:

    def __init__(self, client: DataKitchenClient, name: str) -> None:
        """
        Kitchen object for performing kitchen related API requests.

        Parameters
        ----------
        client : DataKitchenClient
            Client for making requests.
        name : str
            Name of existing kitchen.
        """
        self._client = client
        self._name = name

    @staticmethod
    def create(
            client: DataKitchenClient,
            parent_kitchen_name: str,
            new_kitchen_name: str,
            description: str = ''
    ) -> Kitchen:
        """
        Create a new kitchen and return a kitchen object

        Parameters
        ----------
        client : DataKitchenClient
        parent_kitchen_name : str
            New kitchen will be a child of this parent kitchen
        new_kitchen_name : str
            New kitchen name
        description : str
            New kitchen description

        Returns
        -------
        Kitchen
            :class:`Kitchen <Kitchen>` object
        """
        logger.debug(f'Creating child kitchen of {parent_kitchen_name} named {new_kitchen_name}...')
        client._api_request(
            API_PUT,
            'kitchen',
            'create',
            parent_kitchen_name,
            new_kitchen_name,
            description=description,
        )
        return Kitchen(client, new_kitchen_name)

    def delete(self):
        """
        Delete the current kitchen.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object
        """
        logger.debug(f'Deleting kitchen: {self._name}...')
        return self._client._api_request(API_DELETE, 'kitchen', 'delete', self._name)

    def _get_settings(self):
        """
        Retrieve kitchen settings JSON.

        Returns
        -------
        kitchen_settings : dict
        """
        logger.debug(f'Retrieving settings for kitchen: {self._name}...')
        response = self._client._api_request(API_GET, 'kitchen', self._name)
        return response.json()

    def _update_settings(self, kitchen_settings):
        """
        Update kitchen settings JSON.

        Parameters
        ----------
        kitchen_settings : dict
            Kitchen settings JSON with updated values.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object
        """
        response = self._client._api_request(
            API_POST,
            'kitchen',
            'update',
            kitchen_settings['kitchen']['name'],
            json={"kitchen.json": kitchen_settings['kitchen']}
        )
        return response.json()

    def get_alerts(self):
        """
        Retrieve alerts set on this kitchen.

        Returns
        -------
        alerts : dict
            Dictionary of current kitchen alerts of the form::
                {
                    'Start': ['foo@gmail.com'],
                    'Warning': None,
                    'OverDuration': ['foo@gmail.com', 'bar@gmail.com'],
                    'Success': None,
                    'Failure': ['foo@gmail.com'],
                }
        """
        alerts = self._get_settings()['kitchen']['settings']['alerts']
        return {
            'Start': alerts['orderrunStart'],
            'Warning': alerts['orderrunWarning'],
            'OverDuration': alerts['orderrunOverDuration'],
            'Success': alerts['orderrunSuccess'],
            'Failure': alerts['orderrunError'],
        }

    def add_alerts(self, alerts):
        """
        Add the provided alerts to the kitchen.

        Parameters
        ----------
        alerts : dict
            Alerts to add in the form::

                {
                    'Start': ['foo@gmail.com'],
                    'Warning': None,
                    'OverDuration': ['foo@gmail.com', 'bar@gmail.com'],
                    'Success': None,
                    'Failure': ['foo@gmail.com'],
                }
        """

        kitchen_settings = self._get_settings()
        existing_alerts = kitchen_settings['kitchen']['settings']['alerts']
        for k, v in alerts.items():
            k = 'orderrunError' if k == 'Failure' else f'orderrun{k}'
            if k not in existing_alerts:
                raise KeyError(
                    'Unrecognized alert field: {k}. Expected fields are Start, Warning, OverDuration, Success, and Failure'  # noqa: E501
                )

            if isinstance(v, str):
                v = [v]

            alert_emails = set(existing_alerts[k]) if existing_alerts[k] else set()
            alert_emails = list(alert_emails.union(set(v)))
            existing_alerts[k] = alert_emails

        self._update_settings(kitchen_settings)

    def delete_alerts(self, alerts):
        """
        Delete the provided kitchen alerts.

        Parameters
        ----------
        alerts : dict
            Alerts to delete in the form::

                {
                    'Start': ['foo@gmail.com'],
                    'Warning': None,
                    'OverDuration': ['foo@gmail.com', 'bar@gmail.com'],
                    'Success': None,
                    'Failure': ['foo@gmail.com'],
                }
        """
        kitchen_settings = self._get_settings()

        existing_alerts = kitchen_settings['kitchen']['settings']['alerts']
        for k, v in alerts.items():
            k = 'orderrunError' if k == 'Failure' else f'orderrun{k}'
            if k not in existing_alerts:
                raise KeyError(
                    'Unrecognized alert field: {k}. Expected fields are Start, Warning, OverDuration, Success, and Failure'  # noqa: E501
                )

            if isinstance(v, str):
                v = [v]

            if existing_alerts[k] is not None:
                alert_emails = list(set(existing_alerts[k]) - set(v))
                existing_alerts[k] = alert_emails

        self._update_settings(kitchen_settings)
