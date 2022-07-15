from __future__ import annotations

import logging

from requests import Response
from typing import TYPE_CHECKING

from dkutils.constants import (API_DELETE, API_GET, API_POST, GLOBAL)

from dkutils.datakitchen_api.datakitchen_client import DEFAULT_VAULT_URL

if TYPE_CHECKING:
    from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient

logger = logging.getLogger(__name__)


class Vault:

    def __init__(self, client: DataKitchenClient, kitchen_name: str) -> None:
        """
        Vault object for performing vault related API requests.

        Parameters
        ----------
        client : DataKitchenClient
            Client for making requests.
        kitchen_name : str
            Name of existing kitchen.
        """
        self._client = client
        self._kitchen_name = kitchen_name

    def get_config(self, is_global: bool = False) -> dict:
        """
        Return the vault configuration for the global or kitchen vault.

        Parameters
        ----------
        is_global : boolean, optional
            If True, return global vault config. Otherwise, return kitchen vault config.

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        -------
        dict
            Dictionary of vault config of the form::

                {
                    'inheritable': True,
                    'prefix': 'Acme/development',
                    'private': False,
                    'service': 'custom',
                    'sourceKitchen': 'Development',
                    'url': 'https://vault2.datakitchen.io:8200'
                }
        """
        return self._client._api_request(
            API_GET, "vault", "config", kitchens=self._kitchen_name
        ).json()['config'][GLOBAL if is_global else self._kitchen_name]

    def update_config(
        self,
        prefix: str,
        vault_token: str,
        vault_url: str = DEFAULT_VAULT_URL,
        private: bool = False,
        inheritable: bool = True,
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
        return self._client.update_kitchen_vault(
            prefix,
            vault_token,
            vault_url=vault_url,
            private=private,
            inheritable=inheritable,
        )

    def get_secrets(self, is_global: bool = False):
        """
        Get a list of paths for all the secrets in the kitchen or global vault. No secret values are
        returned.

        Parameters
        ----------
        is_global : boolean, optional
            If True, return global vault secret paths. Otherwise, return kitchen vault secret paths.

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If there is an error retrieving the secrets (e.g. the kitchen does not exist)

        Returns
        ------
        list
            List of secret paths.
        """
        secrets = self._client._api_request(
            API_GET, "secret", kitchens=self._kitchen_name
        ).json()[GLOBAL if is_global else self._kitchen_name]

        if secrets['error']:
            raise ValueError(f'Error retrieving secrets: {secrets["error-message"]}')

        return secrets['list']

    def update_or_add_secret(self, path: str, value: str, is_global: bool = False) -> Response:
        """
        Update an existing secret value or add a new secret if one does not already exist.

        Parameters
        ----------
        path : str
            Path in vault where the secret will be stored.
        value : str
            Value of the secret being stored.
        is_global : boolean, optional
            If True, add to the global vault. Otherwise, add to the kitchen vault.

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        ------
        requests.Response
            :class:`Response <Response>` object
        """
        return self._client._api_request(
            API_POST,
            "secret",
            path,
            kitchen=None if is_global else self._kitchen_name,
            value=value
        )

    def delete_secret(self, path: str, is_global: bool = False) -> Response:
        """
        Delete a secret from vault.

        Parameters
        ----------
        path : str
            Path in vault to the secret being deleted.
        is_global : boolean, optional
            If True, delete from the global vault. Otherwise, delete from the kitchen vault.

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        ------
        requests.Response
            :class:`Response <Response>` object
        """
        return self._client._api_request(
            API_DELETE, "secret", path, kitchen=None if is_global else self._kitchen_name
        )
