from unittest import TestCase
from unittest.mock import patch

from requests.exceptions import HTTPError

from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient
from dkutils.datakitchen_api.recipe import Recipe
from .test_datakitchen_client import (
    DUMMY_USERNAME, DUMMY_PASSWORD, DUMMY_URL, DUMMY_KITCHEN, DUMMY_RECIPE, MockResponse
)

MOCK_RECIPE_FILES_RESPONSE_JSON = {
    'recipes': {
        DUMMY_RECIPE: {
            DUMMY_RECIPE: [{
                'filename': 'README.md',
                'text': 'README contents'
            }, {
                'filename': 'variables.json',
                'json': '{\n    "variable-list": {\n\n    }\n\n}\n',
            }]
        }
    }
}

RECIPE_FILES_DICT_OUTPUT = {
    'README.md': 'README contents',
    'variables.json': '{\n    "variable-list": {\n\n    }\n\n}\n'
}

UPDATE_FILES = {'README.md': 'New README contents', 'new_file.txt': 'New file contents'}

FILES = {
    'README.md': {
        'contents': 'New README contents',
        'isNew': False
    },
    'new_file.txt': {
        'contents': 'New file contents',
        'isNew': True
    }
}

FILEPATHS_TO_DELETE = ['README.md', 'new_file.txt']


class TestRecipe(TestCase):

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def setUp(self, _):
        self.dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, kitchen=DUMMY_KITCHEN, base_url=DUMMY_URL
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipes')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_create_recipe(self, mock_post, get_recipes, _):
        get_recipes.return_value = ['foo']
        Recipe.create(self.dk_client, DUMMY_RECIPE, 'description')
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/recipe/create/{DUMMY_KITCHEN}/{DUMMY_RECIPE}',
            headers=None,
            json={'description': 'description'}
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipes')
    def test_create_recipe_name_exists(self, get_recipes, _):
        get_recipes.return_value = [DUMMY_RECIPE]
        with self.assertRaises(ValueError):
            Recipe.create(self.dk_client, DUMMY_RECIPE, 'description')

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipes')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_create_recipe_raise_http_error(self, mock_post, get_recipes, _):
        get_recipes.return_value = ['foo']
        mock_post.return_value = MockResponse(raise_error=True)
        with self.assertRaises(HTTPError):
            Recipe.create(self.dk_client, DUMMY_RECIPE, 'description')

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.delete')
    def test_delete_recipe(self, mock_delete, _):
        Recipe(self.dk_client, DUMMY_RECIPE).delete(DUMMY_KITCHEN)
        mock_delete.assert_called_with(
            f'{DUMMY_URL}/v2/recipe/{DUMMY_KITCHEN}/{DUMMY_RECIPE}', headers=None, json={}
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    def test_get_recipe_files(self, mock_get, _):
        mock_get.return_value = MockResponse(json=MOCK_RECIPE_FILES_RESPONSE_JSON)
        recipe_files_dict = Recipe(self.dk_client, DUMMY_RECIPE).get_recipe_files(DUMMY_KITCHEN)
        mock_get.assert_called_with(
            f'{DUMMY_URL}/v2/recipe/get/{DUMMY_KITCHEN}/{DUMMY_RECIPE}', headers=None, json={}
        )
        self.assertEqual(RECIPE_FILES_DICT_OUTPUT, recipe_files_dict)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.get')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_update_recipe_files(self, mock_post, mock_get, _):
        mock_get.return_value = MockResponse(json=MOCK_RECIPE_FILES_RESPONSE_JSON)
        Recipe(self.dk_client, DUMMY_RECIPE).update_recipe_files(DUMMY_KITCHEN, UPDATE_FILES)
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/recipe/update/{DUMMY_KITCHEN}/{DUMMY_RECIPE}',
            headers=None,
            json={
                'skipFormat': True,
                'skipCompile': True,
                'files': FILES,
                'message': f'Creating recipe files {FILES.keys()}'
            }
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    @patch('dkutils.datakitchen_api.datakitchen_client.requests.post')
    def test_delete_recipe_files(self, mock_post, _):
        Recipe(self.dk_client, DUMMY_RECIPE).delete_recipe_files(DUMMY_KITCHEN, FILEPATHS_TO_DELETE)
        mock_post.assert_called_with(
            f'{DUMMY_URL}/v2/recipe/update/{DUMMY_KITCHEN}/{DUMMY_RECIPE}',
            headers=None,
            json={
                'skipFormat': True,
                'skipCompile': True,
                'files': {p: {}
                          for p in FILEPATHS_TO_DELETE},
                'message': f'Deleting recipe files {FILEPATHS_TO_DELETE}'
            }
        )
