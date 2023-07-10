from __future__ import annotations

import itertools
import logging
import re

from requests import Response
from typing import TYPE_CHECKING, Union
from collections import defaultdict

from dkutils.constants import (
    API_DELETE,
    API_GET,
    API_POST,
    API_PUT,
)

from dkutils.datakitchen_api.vault import Vault

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
        self._parent_name = None

    @property
    def name(self) -> str:
        """
        Kitchen name
        """
        return self._name

    @property
    def parent_name(self) -> str:
        """
        Parent kitchen name
        """
        if self._parent_name is None:
            self._parent_name = self._get_settings()['kitchen']['parent-kitchen']
        return self._parent_name

    def is_ingredient(self) -> bool:
        """
        Return true if this is an ingredient kitchen, False otherwise.

        Returns
        -------
        bool
            True if this kitchen is an ingredient kitchen, False otherwise.
        """
        match = re.match(pattern=r'(?P<parent_name>\w+)_(?P<uuid>\w{32})', string=self._name)
        return match.group('parent_name') == self.parent_name if match else False

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

        Raises
        ------
        HTTPError
            If the request fails.
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

    def delete(self) -> Response:
        """
        Delete the current kitchen.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object

        Raises
        ------
        HTTPError
            If the request fails.
        """
        logger.debug(f'Deleting kitchen: {self._name}...')
        return self._client._api_request(API_DELETE, 'kitchen', 'delete', self._name)

    def _get_settings(self) -> dict:
        """
        Retrieve kitchen settings JSON.

        Returns
        -------
        settings : dict

        Raises
        ------
        HTTPError
            If the request fails.
        """
        logger.debug(f'Retrieving settings for kitchen: {self._name}...')
        response = self._client._api_request(API_GET, 'kitchen', self._name)
        return response.json()

    def _update_settings(self, settings: dict) -> Response:
        """
        Update kitchen settings JSON.

        Parameters
        ----------
        settings : dict
            Kitchen settings JSON with updated values.

       Returns
        -------
        requests.Response
            :class:`Response <Response>` object

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the name in the given settings does not match that of the current kitchen.
        """
        kitchen_name = settings['kitchen']['name']
        if kitchen_name != self._name:
            raise (
                ValueError(
                    f'Name in settings: {kitchen_name} does not match current kitchen: {self._name}'
                )
            )

        response = self._client._api_request(
            API_POST, 'kitchen', 'update', self._name, json={"kitchen.json": settings['kitchen']}
        )
        return response.json()

    def _get_roles(self, settings: dict = None) -> dict:
        """
        Retrieve the staff and their associated roles assigned to this kitchen.

        Parameters
        ----------
        settings : dict, optional
            Dictionary representing kitchen_settings.json.

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        -------
        roles : dict
            Dictionary of current kitchen staff and their associated roles of the form::

                {
                    'Admin': ['admin@gmail.com'],
                    'Developer': ['developer1@gmail.com', 'developer2@gmail.com'],
                }
        """
        kitchen_settings = settings if settings else self._get_settings()
        kitchen_roles = kitchen_settings['kitchen']['kitchen-roles']
        result = defaultdict(list)
        for email, permission in kitchen_roles.items():
            result[permission].append(email)
        return result

    def _get_staff_set(self, settings: dict = None) -> set:
        """
        Retrieve the set of staff usernames assigned to this kitchen.

        Parameters
        ----------
        settings : dict, optional
            Dictionary representing kitchen_settings.json.

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        -------
        roles : list
            set of current kitchen staff usernames of the form::

                {
                    'admin@gmail.com',
                    'developer1@gmail.com',
                    'developer2@gmail.com',
                }
        """
        _settings = settings if settings else self._get_settings()
        return set(_settings['kitchen']['kitchen-staff'])

    def _ensure_admin(self, roles: dict = None, settings: dict = None) -> None:
        """
        Ensure the user in the provided client has Admin privileges in this kitchen. Otherwise,
        raise a PermissionError.

        Parameters
        ----------
        roles : dict, optional
            Dictionary keyed by role and valued by list of associated usernames.
        settings : dict, optional
            Dictionary representing kitchen_settings.json.

        Raises
        ------
        HTTPError
            If the request fails.
        PermissionError
            If the client user is not an Admin in this kitchen.
        """
        if not roles:
            roles = self._get_roles(settings=settings)

        current_user = self._client._username
        if current_user not in roles['Admin']:
            raise PermissionError(f'Current user ({current_user}) not an Admin. Permission denied.')

    def _ensure_disjoint(self, lists: list) -> bool:
        """
        Return True if all the provided lists (converted to sets) are disjoint, False otherwise.

        Parameters
        ----------
        lists : list
            List of lists. Each list will be converted to a set to ensure they are all disjoint.

        Returns
        -------
        bool
            True if provided lists are disjoint, False otherwise.
        """
        if len(lists) > 1:
            merged_set = set(lists[0])
            for l in lists[1:]:
                if not merged_set.isdisjoint(set(l)):
                    return False
                merged_set = merged_set | set(l)
        return True

    def get_alerts(self) -> dict:
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

    def add_alerts(self, alerts: dict) -> None:
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

        Raises
        ------
        KeyError
            If an unrecognized alert field is provided - valid fields are Start, Warning,
            OverDuration, Success, and Failure
        """

        settings = self._get_settings()
        existing_alerts = settings['kitchen']['settings']['alerts']
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

        self._update_settings(settings)

    def delete_alerts(self, alerts: dict) -> None:
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

        Raises
        ------
        KeyError
            If an unrecognized alert field is provided - valid fields are Start, Warning,
            OverDuration, Success, and Failure
        """
        settings = self._get_settings()

        existing_alerts = settings['kitchen']['settings']['alerts']
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

        self._update_settings(settings)

    def get_staff(self) -> dict:
        """
        Retrieve the staff and their associated roles assigned to this kitchen.

        Raises
        ------
        HTTPError
            If the request fails.
        PermissionError
            If the current user is not an Admin

        Returns
        -------
        staff : dict
            Dictionary of current kitchen staff and their associated roles of the form::

                {
                    'Admin': ['admin@gmail.com'],
                    'Developer': ['developer1@gmail.com', 'developer2@gmail.com'],
                }
        """
        return self._get_roles()

    def ensure_users_is_part_of_staff(
            self, users_to_check: Union[set, list], current_staff: Union[set, list] = None
    ) -> None:
        """
        Ensure a list of users is part of Kitchen Staff. Otherwise, raise a ValueError.

        Parameters
        ----------
        users_to_check : set or list
            List or set of emails of the users to check if they are part of the staff.
        current_staff : set or list
            List or set of the current staff.
        Raises
        ------
        ValueError
            If the users to check are not part of the Kitchen Staff.

        """
        if not current_staff:
            current_staff = self._get_staff_set()

        if not users_to_check.issubset(current_staff):
            raise ValueError(
                f'The following staff do not already exist in kitchen: {users_to_check - current_staff}'
            )
        pass

    def delete_staff(self, staff_to_delete: Union[set, list]) -> Response:
        """
        Delete the provided staff from this kitchen.

        Parameters
        ----------
        staff_to_delete : set or list
            List or set of usernames to delete from this kitchen's staff.

        Raises
        ------
        HTTPError
            If the request fails.
        PermissionError
            If the current user is not an Admin

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object
        """
        if not isinstance(staff_to_delete, set):
            staff_to_delete = set(staff_to_delete)

        settings = self._get_settings()
        self._ensure_admin(settings=settings)

        current_staff = self._get_staff_set(settings)
        self.ensure_users_is_part_of_staff(staff_to_delete, current_staff)

        # Remove staff from list
        settings['kitchen']['kitchen-staff'] = list(current_staff - staff_to_delete)

        # Remove staff from roles
        for staff in staff_to_delete:
            if staff in settings['kitchen']['kitchen-roles']:
                del settings['kitchen']['kitchen-roles'][staff]

        return self._update_settings(settings)

    def add_staff(self, staff_to_add: dict) -> Response:
        """
        Add the provided staff to this kitchen.

        Parameters
        ----------
        staff_to_add : dict
            Dictionary keyed by role and valued with list of users to add to that role in the form::

                {
                    'Admin': ['admin@gmail.com'],
                    'Developer': ['developer1@gmail.com', 'developer2@gmail.com'],
                }

        Raises
        ------
        HTTPError
            If the request fails.
        PermissionError
            If the current user is not an Admin
        ValueError
            If the provided staff are not new or unique across roles.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object
        """
        if not self._ensure_disjoint(list(staff_to_add.values())):
            raise ValueError(f'Staff lists for each role must be unique.')

        settings = self._get_settings()
        self._ensure_admin(settings=settings)

        # Add staff to list
        current_staff = self._get_staff_set(settings)
        new_staff = set(itertools.chain.from_iterable(staff_to_add.values()))

        if not current_staff.isdisjoint(new_staff):
            raise ValueError(
                f'The following staff already exist in kitchen: {current_staff & new_staff}'
            )

        settings['kitchen']['kitchen-staff'] = list(current_staff | new_staff)

        # Add staff to roles
        for role, list_of_staff_to_add in staff_to_add.items():
            for staff_to_add in list_of_staff_to_add:
                settings['kitchen']['kitchen-roles'][staff_to_add] = role

        return self._update_settings(settings)

    def update_staff(self, staff_to_update: dict) -> Response:
        """
        Update roles for the provided staff to this kitchen.

        Parameters
        ----------
        staff_to_update : dict
            Dictionary keyed by role and valued with list of users to update to that role in the form::

                {
                    'Admin': ['admin@gmail.com'],
                    'Developer': ['developer1@gmail.com', 'developer2@gmail.com'],
                }

        Raises
        ------
        HTTPError
            If the request fails.
        PermissionError
            If the current user is not an Admin
        ValueError
            If the provided staff are not new or unique across roles.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object
        """
        if not self._ensure_disjoint(list(staff_to_update.values())):
            raise ValueError(f'Staff lists for each role must be unique.')

        settings = self._get_settings()
        self._ensure_admin(settings=settings)

        # Add staff to list
        current_staff = self._get_staff_set(settings)
        updated_staff = set(itertools.chain.from_iterable(staff_to_update.values()))

        self.ensure_users_is_part_of_staff(updated_staff, current_staff)

        # Update staff to roles
        for role, list_staff in staff_to_update.items():
            for staff in list_staff:
                settings['kitchen']['kitchen-roles'][staff] = role

        return self._update_settings(settings)

    def get_vault(self):
        return Vault(self._client, self._name)
