from . import LOGGER


def validate_globals(global_variables):
    """
    Validate that the list of provided global variable names exist in the global namespace
    and have defined values.

    Parameters
    ----------
    global_variables : array
      Array of global variable names to test for existence.

    Raises
    -------
    NameError
        If global variable is undefined.
    """
    undefined_globals = []
    for var in global_variables:
        if var not in globals() or not globals()[var]:
            LOGGER.error(f'Undefined global variable: {var}')
            undefined_globals.append(var)

    if undefined_globals:
        raise NameError(f'Undefined global variables: {undefined_globals}')

