from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from dkutils.constants import (
    API_DELETE,
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
            Client for making requests .
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
        response = client._api_request(
            API_PUT,
            'kitchen',
            'create',
            parent_kitchen_name,
            new_kitchen_name,
            description=description,
        )
        response.raise_for_status()
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
        response = self._client._api_request(API_DELETE, 'kitchen', 'delete', self._name)
        response.raise_for_status()
        return response
