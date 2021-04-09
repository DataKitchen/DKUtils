import csv
import json
import logging

from dataclasses import dataclass
from pathlib import Path
from typing import List

from dkutils.constants import VALID_TEST_DIRECTORIES

logger = logging.getLogger(__name__)


@dataclass
class TestInfo:
    test: str
    datestamp: str
    description: str
    kitchen: str
    recipe: str
    node: str
    failure_action: str
    variable: str
    metric: str
    comparison: str
    expression: str

    @classmethod
    def keys(cls):
        return cls.__dataclass_fields__.keys()

    def get(self, field_name, default=None):
        return getattr(self, field_name, default)


def is_valid_test_directory(base_path, file_depth) -> bool:
    """
    Only node directories and their immediate subdirectories may contain tests. This function takes
    a recipe subdirectory and returns True if it may contain tests or False otherwise.

    Parameters
    ----------
    base_path : Path
        Recipe subdirectory path that may or may not contain tests. This path is relative to a
        recipe's root directory (e.g. Recipe/Node/data_sinks).
    file_depth : int
        Depth of directory containing recipe files (e.g. Recipe/Node/notebook.json has
        file_depth==2). Tests may only be defined in files in the root of a node directory or
        direct subdirectories (i.e. file_depth == 2 or 3)

    Returns
    -------
    boolean
        True if the recipe base_path may contain tests, False otherwise.
    """
    if file_depth < 2 or file_depth > 3:
        return False

    # base_path starts with the recipe name, followed by node name (e.g. Recipe/Node or
    # Recipe/resources)
    node_name = base_path.parts[1]

    # Ignore the resources directory
    if node_name == 'resources':
        return False

    # Only certain node subdirectories may contain tests
    return file_depth != 3 or base_path.parts[2] in VALID_TEST_DIRECTORIES


def is_valid_test_file(file_path, file_depth) -> bool:
    """
    Only certain files may contain tests. This function returns True if the provided file may
    contain tests or False otherwise.

    Parameters
    ----------
    file_path : Path
        Path to a recipe file relative to the root of the recipe (e.g. Recipe/Node/notebook.json)
    file_depth : int
        Subdirectory depth of recipe file (e.g. Recipe/Node/notebook.json file depth is 2)

    Returns
    -------
    boolean
        True if the file may contain tests, otherwise False.
    """
    if file_path.name == 'notebook.json':
        return True
    return file_depth == 3 and file_path.suffix == '.json'


def get_recipe_test_paths(client, kitchen=None, recipe=None) -> List[str]:
    """
    Return a list of paths to all recipe files that potentially contain tests. The kitchen and
    and recipe that are interrogated for tests are derived from the client, unless otherwise
    specified as optional input arguments. If kitchen and/or recipe arguments are provided, they
    are set accordingly on the provided client.

    Parameters
    ----------
    client : DataKitchenClient
        DataKitchenClient instance with kitchen and/or recipe set accordingly, unless optional
        kitchen and/or recipe arguments are provided
    kitchen : str, optional
        If None, use the kitchen currently set on the client, otherwise set the kitchen accordingly.
    recipe : str, optional
        If None, use the recipe currently set on the client, otherwise, set the recipe accordingly.

    Returns
    -------
    list
        List of paths to all recipe files that potentially contain tests.
    """
    if kitchen:
        client.kitchen = kitchen

    if recipe:
        client.recipe = recipe

    logger.info(f'Finding test files in recipe: {client.recipe}')
    json_response = client.get_recipe(recipe_files=['description.json'], include_recipe_tree=True)

    test_paths = []
    for recipe_contents in json_response['recipe-tree'].values():
        for file_dir, files in recipe_contents.items():
            base_path = Path(file_dir)
            file_depth = len(base_path.parts)

            if is_valid_test_directory(base_path, file_depth):
                for file_info in files:
                    file_path = base_path / file_info["filename"]
                    if is_valid_test_file(file_path, file_depth):
                        # Remove recipe name from start of file path and path separator
                        test_paths.append(str(file_path)[len(client.recipe) + 1:])
    logger.info(f'Finished finding test files in recipe: {client.recipe}')
    return test_paths


def extract_tests_from_files(client,
                             datestamp,
                             test_paths,
                             kitchen=None,
                             recipe=None) -> List[TestInfo]:
    """
    Extract tests from the provided test_paths. The kitchen and recipe are derived from the client,
    unless otherwise specified as optional input arguments. If kitchen and/or recipe arguments are
    provided, they are set accordingly on the provided client.

    Parameters
    ----------
    client : DataKitchenClient
        DataKitchenClient instance with kitchen and/or recipe set accordingly, unless optional
        kitchen and/or recipe arguments are provided
    datestamp : datetime
        Datestamp indicating approximate time when tests were extracted.
    test_paths : list
        List of paths to all recipe files that potentially contain tests.
    kitchen : str, optional
        If None, use the kitchen currently set on the client, otherwise set the kitchen accordingly.
    recipe : str, optional
        If None, use the recipe currently set on the client, otherwise, set the recipe accordingly.

    Returns
    -------
    list
        List of TestInfo objects, one per test found in the provided test_paths.
    """
    if kitchen:
        client.kitchen = kitchen

    if recipe:
        client.recipe = recipe

    logger.info(f'Extracting tests from files in recipe: {client.recipe}')
    try:
        json_response = client.get_recipe(recipe_files=test_paths, include_recipe_tree=False)
    except Exception:
        logger.error(f'Failed to retrieve recipe files containing tests: {test_paths}')
        raise

    test_infos = []
    for recipe_contents in json_response['recipes'].values():
        for file_dir, files in recipe_contents.items():
            base_path = Path(file_dir)
            node_name = base_path.parts[1]
            logger.info(f'Processing node: {node_name}')

            for file_info in files:
                if 'json' not in file_info:
                    logger.info(
                        f"JSON field not present in node {node_name}'s file {file_info['filename']}"
                    )
                    continue

                json_contents = json.loads(file_info['json'])
                try:
                    if 'tests' in json_contents:
                        for test, fields in json_contents['tests'].items():
                            description = fields['description'] if 'description' in fields else ''

                            metric = ''
                            comparison = ''
                            expression = ''
                            if isinstance(fields['test-logic'], dict):
                                metric = fields['test-logic']['test-metric']
                                comparison = fields['test-logic']['test-compare']
                            else:
                                expression = fields['test-logic']

                            test_infos.append(
                                TestInfo(
                                    **{
                                        'test': test,
                                        'datestamp': datestamp,
                                        'description': description,
                                        'kitchen': client.kitchen,
                                        'recipe': client.recipe,
                                        'node': node_name,
                                        'failure_action': fields['action'],
                                        'variable': fields['test-variable'],
                                        'metric': metric,
                                        'comparison': comparison,
                                        'expression': expression,
                                    }
                                )
                            )
                except Exception as e:
                    logger.info(
                        f'Failed to parse tests from {base_path / file_info["filename"]}: {str(e)}'
                    )

            logger.info(f'Finished processing node: {node_name}')
    logger.info(f'Finished extracting tests from files in recipe: {client.recipe}')
    return test_infos


def get_test_infos(client, datestamp, recipes, kitchen=None) -> List[TestInfo]:
    """
    For a set of recipes in a kitchen, retrieve all the defined tests and their associated metadata.
    Return a list of test_info dictionaries, one per test.

    Parameters
    ----------
    client : DataKitchenClient
        DataKitchenClient instance with kitchen set accordingly, unless optional
        kitchen argument is provided
    datestamp : datetime
        Datestamp indicating approximate time when tests were extracted.
    recipes : list
        List of paths to all recipe files that potentially contain tests.
    kitchen : str, optional
        If None, use the kitchen currently set on the client, otherwise set the kitchen accordingly.

    Returns
    -------
    list
        List of TestInfo objects, one per test found in the provided kitchen recipes.
    """
    if kitchen:
        client.kitchen = kitchen

    logger.info(f'Finding tests in kitchen: {kitchen}')
    test_infos = []
    for recipe in recipes:
        test_paths = get_recipe_test_paths(client, recipe=recipe)
        test_infos.extend(extract_tests_from_files(client, datestamp, test_paths))
    return test_infos


def write_test_infos_csv(test_infos, output_csv_path) -> None:
    """
    Write a list of TestInfo objects to a CSV file.

    Parameters
    ----------
    test_infos : list
        List of TestInfo object
    output_csv_path : str
        Output CSV file path
    """
    with open(output_csv_path, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=TestInfo.keys())
        writer.writeheader()
        writer.writerows(test_infos)
