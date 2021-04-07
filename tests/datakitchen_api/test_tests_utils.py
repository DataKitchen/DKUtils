import json

from nose.tools import nottest
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient
from dkutils.datakitchen_api.tests_utils import (
    extract_tests_from_files,
    get_recipe_test_paths,
    get_test_infos,
    is_valid_test_directory,
    is_valid_test_file,
    write_test_infos_csv,
)

from .test_datakitchen_client import (
    DUMMY_USERNAME,
    DUMMY_PASSWORD,
    DUMMY_KITCHEN,
    DUMMY_URL,
)

extract_tests_from_files = nottest(extract_tests_from_files)
get_recipe_test_paths = nottest(get_recipe_test_paths)
get_test_infos = nottest(get_test_infos)
is_valid_test_directory = nottest(is_valid_test_directory)
is_valid_test_file = nottest(is_valid_test_file)
write_test_infos_csv = nottest(write_test_infos_csv)

DATESTAMP = '2021-04-07 12:36:01.047096'
PARENT_DIR = Path(__file__).parent
VALID_TEST_PATH_1 = Path('Recipe/Node/notebook.json')
VALID_TEST_PATH_2 = Path('Recipe/Node/actions/foo.json')
RESOURCES_TEST_PATH = Path('Recipe/resources/foo.json')
INVALID_TEST_PATH_DIRNAME = Path('Recipe/Node/foo/notebook.json')
INVALID_TEST_PATH_DEPTH = Path('Recipe/Node/actions/foo/foo.json')
INVALID_TEST_PATH_FILENAME = Path('Recipe/Node/actions/foo.txt')

EXPECTED_TEST_PATHS = [
    'Add_Schema_and_Tables/notebook.json', 'Add_Schema_and_Tables/actions/source.json',
    'Delete_Schema/notebook.json', 'Delete_Schema/actions/source.json',
    'Forecast_Walmart_Sales/notebook.json', 'Forecast_Walmart_Sales/data_sinks/s3_datasink.json',
    'Forecast_Walmart_Sales/data_sources/redshift_datasource.json',
    'Forecast_Walmart_Sales/data_sources/source.json',
    'Load_Forecasted_Walmart_Sales_Data/notebook.json',
    'Load_Forecasted_Walmart_Sales_Data/actions/source.json',
    'Load_Walmart_Sales_Data/notebook.json', 'Load_Walmart_Sales_Data/actions/source.json',
    'Retrieve_Walmart_Sales_Data/notebook.json', 'Retrieve_Walmart_Sales_Data/data_sinks/sink.json',
    'Retrieve_Walmart_Sales_Data/data_sources/source.json', 'Train_Model/notebook.json',
    'Train_Model/data_sinks/s3_datasink.json', 'Train_Model/data_sources/source.json'
]


class TestTestsUtilsNoClient(TestCase):

    def test_is_valid_test_directory_1(self):
        base_path = VALID_TEST_PATH_1.parent
        file_depth = len(base_path.parts)
        self.assertTrue(is_valid_test_directory(base_path, file_depth))

    def test_is_valid_test_directory_2(self):
        base_path = VALID_TEST_PATH_2.parent
        file_depth = len(base_path.parts)
        self.assertTrue(is_valid_test_directory(base_path, file_depth))

    def test_is_valid_test_directory_invalid_filename(self):
        base_path = INVALID_TEST_PATH_DIRNAME.parent
        file_depth = len(base_path.parts)
        self.assertFalse(is_valid_test_directory(base_path, file_depth))

    def test_is_valid_test_directory_invalid_depth(self):
        base_path = INVALID_TEST_PATH_DEPTH.parent
        file_depth = len(base_path.parts)
        self.assertFalse(is_valid_test_directory(base_path, file_depth))

    def test_is_valid_test_directory_resources(self):
        base_path = RESOURCES_TEST_PATH.parent
        file_depth = len(base_path.parts)
        self.assertFalse(is_valid_test_directory(base_path, file_depth))

    def test_is_valid_test_file_1(self):
        file_depth = len(VALID_TEST_PATH_1.parent.parts)
        self.assertTrue(is_valid_test_file(VALID_TEST_PATH_1, file_depth))

    def test_is_valid_test_file_2(self):
        file_depth = len(VALID_TEST_PATH_2.parent.parts)
        self.assertTrue(is_valid_test_file(VALID_TEST_PATH_2, file_depth))

    def test_is_valid_test_file_(self):
        file_depth = len(INVALID_TEST_PATH_FILENAME.parent.parts)
        self.assertFalse(is_valid_test_file(INVALID_TEST_PATH_FILENAME, file_depth))


class TestTestsUtils(TestCase):

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient._validate_token')
    def setUp(self, _):
        self.dk_client = DataKitchenClient(
            DUMMY_USERNAME, DUMMY_PASSWORD, kitchen=DUMMY_KITCHEN, base_url=DUMMY_URL
        )

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipe')
    def test_get_recipe_test_paths(self, mock_get_recipe):
        self.dk_client.recipe = 'Training_Sales_Forecast'
        with open(PARENT_DIR.joinpath('get_recipe_with_tests.json')) as json_file:
            mock_get_recipe.return_value = json.load(json_file)
        self.assertListEqual(EXPECTED_TEST_PATHS, get_recipe_test_paths(self.dk_client))

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipe')
    def test_get_recipe_test_paths_no_test_paths(self, mock_get_recipe):
        self.dk_client.recipe = 'Recipe_Test'
        with open(PARENT_DIR.joinpath('get_recipe_readme_with_tree.json')) as json_file:
            mock_get_recipe.return_value = json.load(json_file)
        self.assertListEqual([], get_recipe_test_paths(self.dk_client, kitchen='Foo'))
        self.assertEqual('Foo', self.dk_client.kitchen)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipe')
    def test_extract_tests_from_files(self, mock_get_recipe):
        self.dk_client.recipe = 'Training_Sales_Forecast'
        with open(PARENT_DIR.joinpath('get_recipe_only_test_files_no_tree.json')) as json_file:
            mock_get_recipe.return_value = json.load(json_file)
        test_infos = extract_tests_from_files(self.dk_client, DATESTAMP, EXPECTED_TEST_PATHS)
        self.assertEqual(len(test_infos), 16)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipe')
    def test_extract_tests_from_files_provide_kitchen_and_recipe(self, mock_get_recipe):
        with open(PARENT_DIR.joinpath('get_recipe_only_test_files_no_tree.json')) as json_file:
            mock_get_recipe.return_value = json.load(json_file)
        test_infos = extract_tests_from_files(
            self.dk_client,
            DATESTAMP,
            EXPECTED_TEST_PATHS,
            kitchen='Foo',
            recipe='Training_Sales_Forecast'
        )
        self.assertEqual(len(test_infos), 16)
        self.assertEqual('Foo', self.dk_client.kitchen)
        self.assertEqual('Training_Sales_Forecast', self.dk_client.recipe)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipe')
    def test_get_test_infos(self, mock_get_recipe):
        side_effects = []
        with open(PARENT_DIR.joinpath('get_recipe_with_tests.json')) as json_file:
            side_effects.append(json.load(json_file))
        with open(PARENT_DIR.joinpath('get_recipe_only_test_files_no_tree.json')) as json_file:
            side_effects.append(json.load(json_file))
        mock_get_recipe.side_effect = side_effects
        recipes = ['Training_Sales_Forecast']
        test_infos = get_test_infos(self.dk_client, DATESTAMP, recipes, kitchen='Foo')
        self.assertEqual(len(test_infos), 16)
        self.assertEqual('Foo', self.dk_client.kitchen)

    @patch('dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_recipe')
    def test_write_test_infos_csv(self, mock_get_recipe):
        side_effects = []
        with open(PARENT_DIR.joinpath('get_recipe_with_tests.json')) as json_file:
            side_effects.append(json.load(json_file))
        with open(PARENT_DIR.joinpath('get_recipe_only_test_files_no_tree.json')) as json_file:
            side_effects.append(json.load(json_file))
        mock_get_recipe.side_effect = side_effects
        recipes = ['Training_Sales_Forecast']
        test_infos = get_test_infos(self.dk_client, DATESTAMP, recipes)
        expected_test_infos_path = PARENT_DIR / 'expected_test_infos.csv'
        observed_test_infos_path = PARENT_DIR / 'observed_test_infos.csv'
        write_test_infos_csv(test_infos, observed_test_infos_path)
        with open(expected_test_infos_path) as expected_file, \
                open(observed_test_infos_path) as observed_file:
            self.assertListEqual(expected_file.readlines(), observed_file.readlines())
