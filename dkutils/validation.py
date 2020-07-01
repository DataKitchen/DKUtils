import inspect

from dkutils.constants import CHANGE_ME


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
