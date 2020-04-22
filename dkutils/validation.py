import inspect


def validate_globals(global_var_names):
    """
    Validate that the list of provided global variable names exist in the global namespace
    of the calling function.

    Parameters
    ----------
    global_var_names : array
      Array of global variable names to test for existence.

    Raises
    -------
    NameError
        If any global variables do not exist in the global namespace of the calling function.
    """
    undefined_globals = []

    # https://docs.python.org/3/library/inspect.html#inspect.stack
    cur_globals = inspect.stack()[1][0].f_globals

    for var in global_var_names:
        if var not in cur_globals:
            print(f'Undefined global variable: {var}')
            undefined_globals.append(var)

    if undefined_globals:
        raise NameError(f'Undefined global variables: {undefined_globals}')
