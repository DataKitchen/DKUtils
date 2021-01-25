import inspect
import json
import logging
import os
import pathlib
from typing import Dict, Union

from dkutils.constants import CHANGE_ME

GLOBALS_CONFIG_PATH: pathlib.Path = pathlib.Path(os.getcwd()) / 'globals_config.json'
ConfigDict = Dict[str, Union[str, int]]


def get_globals_config(global_var_names, cur_globals):
    """
    Load the specified glabal variables from a file named globals_config.json if it exists. This is to facillitate
    a way of initializing the globals variables when running the code outside of DataKitchen. These global variables
    would normally be passed from DataKitchen.
    Parameters
    ----------
    global_var_names :
        list of global variable names to initialize
    cur_globals
        list of currently defined global variables
    """
    if GLOBALS_CONFIG_PATH.is_file():
        with GLOBALS_CONFIG_PATH.open() as cfg:
            config: ConfigDict = json.load(cfg)
        for var in global_var_names:
            if var in config:
                cur_globals[var] = config.get(var)


def validate_globals(global_var_names):
    """
    Validate that the list of provided global variable names exist in the global namespace
    of the calling function.

    Parameters
    ----------
    global_var_names : list
      list of global variable names to test for existence.

    Raises
    -------
    NameError
        If any global variables do not exist in the global namespace of the calling function.
        If any global variables exist in the global namespace of the calling function with the value '[CHANGE_ME]'
    """
    undefined_globals = []
    need_to_be_changed = []

    # https://docs.python.org/3/library/inspect.html#inspect.stack
    cur_globals = inspect.stack()[1][0].f_globals
    get_globals_config(global_var_names, cur_globals)
    for var in global_var_names:
        if var not in cur_globals:
            print(f'Undefined global variable: {var}')
            undefined_globals.append(var)
        elif CHANGE_ME == cur_globals[var]:
            need_to_be_changed.append(var)

    if undefined_globals or need_to_be_changed:
        msg = ''
        if undefined_globals:
            msg += f'\n\tUndefined global variables: {undefined_globals}'
        if need_to_be_changed:
            msg += f'\n\tGlobal variables with values that need to be changed: {need_to_be_changed}'
        raise NameError(msg)


def skip_token_validation():
    """
    Determine if the outgoing API request should validate the current auth token and
    refresh it if invalid.

    Returns
    -------
    boolean
        True if current request can skip token validation, False otherwise.
    """
    skip_methods = ['_validate_token', '_refresh_token']
    return inspect.stack()[2][3] in skip_methods


def get_max_concurrency(num_orders, max_concurrent):
    """
    Given a specified maximum concurrency and the number of orders being created/resumed, return
    a valid maximum concurrency value (i.e. 1 <= max_concurrent <= num_orders). If max_concurrent
    is None, return num_orders.

    Parameters
    ----------
    num_orders : int
        Number of orders to be created/resumed.
    max_concurrent
        Maximum number of orders to process concurrently

    Returns
    -------
    int
        Valid maximum concurrency (i.e. 1 <= max_concurrent <= num_orders) or num_orders if
        max_concurrent is None.

    """
    if max_concurrent is None:
        return num_orders
    elif max_concurrent < 1:
        return 1
    return min(num_orders, max_concurrent)


def ensure_pathlib(path):
    """
    If provided path is a pathlib.PurePath instance, return it. If it's a string, convert it to a
    pathlib.PurePath instance and return it. Otherwise, raise a TypeError.

    Parameters
    ----------
    path : str or pathlib.PurePath
        Path to be returned as a pathlib.PurePath instance.

    Raises
    ------
    TypeError
        If provided path is neither a string nor a pathlib.PurePath instance.

    Returns
    -------
    pathlib.PurePath
    """
    if isinstance(path, str):
        return pathlib.Path(path)
    elif not isinstance(path, pathlib.PurePath):
        raise TypeError(f'Expected str or pathlib.PurePath type, but found {type(path)}')
    return path


def set_logging_level(logging_level=logging.INFO):
    """
    Set the logging level for the logger in the global variable LOGGER. If the global variable LOOGER does
    not exist it will be set to a logger obtained from the logging library. This is to allow code to be run
    outside of DataKitchen without the need to add code to initialize the global variable LOGGER has is done
    by DataKitchen.make
    Parameters
    ----------
    logging_level: str, optional

    Returns
    -------

    """
    logger_name = "LOGGER"
    cur_globals = inspect.stack()[1][0].f_globals
    logger = cur_globals.get(logger_name)
    if not logger:
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        cur_globals[logger_name] = logger
    logger.setLevel(logging_level)
