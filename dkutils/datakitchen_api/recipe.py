from __future__ import annotations

import logging
import os

from requests import Response
from typing import TYPE_CHECKING
from pathlib import Path

from dkutils.constants import (
    API_DELETE,
    API_GET,
    API_POST,
    KITCHEN,
)

if TYPE_CHECKING:
    from .datakitchen_client import DataKitchenClient

logger = logging.getLogger(__name__)


class NodeNotFoundError(FileNotFoundError):
    pass


class Recipe:

    def __init__(self, client: DataKitchenClient, name: str) -> None:
        """
        Recipe object for performing recipe related API requests.

        Parameters
        ----------
        client : DataKitchenClient
            Client for making requests .
        name : str
            Name of existing recipe.
        """
        self._client = client
        self._name = name

    @property
    def name(self):
        return self._name

    @staticmethod
    def create(client: DataKitchenClient, recipe_name: str, description: str = None) -> Recipe:
        """
        Create a new recipe in the kitchen set on the provided client and return a Recipe object

        Parameters
        ----------
        client : DataKitchenClient
            Client for making requests.
        recipe_name : str
            New recipe name
        description : str
            New recipe description

        Returns
        -------
        Recipe
            :class:`Recipe <Recipe>` object

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If recipe_name is empty or None
            If recipe_name already exists in the provided kitchen
        """
        logger.debug(f'Creating recipe named {recipe_name} in kitchen {client.kitchen}...')
        client._ensure_attributes(KITCHEN)

        if not recipe_name:
            raise ValueError('Recipe name cannot be empty or None')

        # Ensure recipe doesn't already exist
        recipes = client.get_recipes()
        if recipe_name in recipes:
            raise ValueError(f'Recipe {recipe_name} already exists in kitchen {client.kitchen}')

        client._api_request(
            API_POST, 'recipe', 'create', client.kitchen, recipe_name, description=description
        )
        return Recipe(client, recipe_name)

    def delete(self, kitchen_name: str) -> Response:
        """
        Delete this recipe from the provided kitchen.

        Parameters
        ----------
        kitchen_name : str
            Kitchen from which the recipe will be deleted.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object

        Raises
        ------
        HTTPError
            If the request fails.
       """
        logger.debug(f'Deleting recipe named {self.name} in kitchen {kitchen_name}...')
        return self._client._api_request(API_DELETE, 'recipe', kitchen_name, self.name)

    def get_recipe_files(self, kitchen_name: str) -> dict:
        """
        Retrieve all the files for this recipe in the provided kitchen.

        Parameters
        ----------
        kitchen_name : str
            Kitchen from which the recipe files will be retrieved.

        Returns
        -------
        dict
            Dictionary keyed by file path and valued by file contents string.

        Raises
        ------
        HTTPError
            If the request fails.
        Exception
            If a filetype is unrecognized.
        """
        logger.debug(f'Retrieving files for recipe {self.name} in kitchen {kitchen_name}...')
        response = self._client._api_request(API_GET, 'recipe', 'get', kitchen_name, self.name)

        recipe_files_dict = {}
        for path, file_details_array in response.json()['recipes'][self.name].items():

            # Strip recipe name from filepath
            root_path = Path(*Path(path).parts[1:])

            for file_details in file_details_array:
                filepath = str(root_path / file_details['filename'])
                if 'text' in file_details:
                    recipe_files_dict[filepath] = file_details['text']
                elif 'json' in file_details:
                    recipe_files_dict[filepath] = file_details['json']
                else:
                    raise Exception(
                        f'Unrecognized file type for {filepath}: accepted types are TEXT or JSON'
                    )

        return recipe_files_dict

    def get_node_files(self, kitchen_name: str, nodes: list) -> dict:
        """
        Retrieve all the files associated with the provided list of nodes.

        Parameters
        ----------
        kitchen_name : str
            Kitchen from which the recipe node files will be retrieved.
        nodes : list
            List of node names

        Raises
        ------
        HTTPError
            If the request fails.
        NodeNotFoundError
            If any of the provided nodes do not exist in this recipe.

        Returns
        -------
        dict
            Dictionary keyed by file path and valued by file contents.
        """
        recipe_files = self.get_recipe_files(kitchen_name)

        # Ensure the nodes being retrieved actually exist in this recipe
        available_nodes = {f.split(os.sep)[0] for f in recipe_files.keys() if os.sep in f}
        missing_nodes = set(nodes) - available_nodes
        if len(missing_nodes) > 0:
            raise NodeNotFoundError(
                f'The following nodes do not exist in kitchen {kitchen_name} and recipe {self.name}: {list(missing_nodes)}'  # noqa: E501
            )

        return {
            path: recipe_files[path]
            for path in recipe_files.keys()
            if os.sep in path and path.split(os.sep)[0] in nodes
        }

    def update_recipe_files(self, kitchen_name: str, filepaths: dict) -> Response:
        """
        Update the files for this recipe in the provided kitchen.

        Parameters
        ----------
        kitchen_name : str
            Kitchen for which the recipe files will be updated.
        filepaths : dict
            Dictionary keyed by file path and valued by new/updated file contents.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object

        Raises
        ------
        HTTPError
            If the request fails.
        """
        logger.debug(
            f'Updating files ({list(filepaths.keys())}) for recipe {self.name} in kitchen {kitchen_name}...'
        )

        # Retrieve all the existing files in the recipe
        recipe_files = self.get_recipe_files(kitchen_name)

        files = {}
        for p, c in filepaths.items():
            files[p] = {'contents': c, 'isNew': False if p in recipe_files else True}

        return self._client._api_request(
            API_POST,
            'recipe',
            'update',
            kitchen_name,
            self.name,
            skipFormat=True,
            skipCompile=True,
            files=files,
            message=f'Creating recipe files {files.keys()}'
        )

    def delete_recipe_files(self, kitchen_name: str, filepaths: list) -> Response:
        """
        Delete the provided files from this recipe in the provided kitchen.

        Parameters
        ----------
        kitchen_name : str
            Kitchen from which the recipe files will be deleted.
        filepaths : list
            List of file paths to delete.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object

        Raises
        ------
        HTTPError
            If the request fails.
        """
        logger.debug(
            f'Deleting files ({filepaths}) for recipe {self.name} in kitchen {kitchen_name}...'
        )

        # Including an empty dictionary for a file path implies file deletion
        files = {p: {} for p in filepaths}

        return self._client._api_request(
            API_POST,
            'recipe',
            'update',
            kitchen_name,
            self.name,
            skipFormat=True,
            skipCompile=True,
            files=files,
            message=f'Deleting recipe files {filepaths}'
        )
