import requests

DEFAULT_DATAKITCHEN_URL = 'https://cloud.datakitchen.io'


def get_headers(username, password, datakitchen_url=DEFAULT_DATAKITCHEN_URL):
    """
    Login to the DataKitchen platform via the login API to retrieve a token. Store the \
    token in headers required to make subsequent API requests.

    Parameters
    ----------
    username : str
      DataKitchen platform username.
    password : str
      DataKitchen platform password.
    datakitchen_url : str, optional
        DataKitchen platform URL (default is https://cloud.datakitchen.io)

    Raises
    ------
    HTTPError
        If the request fails.

    Returns
    -------
    dict
        Dictionary of headers required by subsequent API requests
    """
    credentials = dict()
    credentials['username'] = username
    credentials['password'] = password

    login_url = f'{datakitchen_url}/v2/login'
    response = requests.post(login_url, data=credentials)
    response.raise_for_status()
    return {'Authorization': f'Bearer {response.text}'}


def create_order(
    headers, kitchen, recipe, variation, parameters={}, datakitchen_url=DEFAULT_DATAKITCHEN_URL
):
    """

    Parameters
    ----------
    headers : dict
        Headers containing authentication token.
    kitchen :  str
        Kitchen name
    recipe : str
        Recipe name
    variation : str
        Variation name
    parameters : dict, optional
        Dictionary of variable overrides (default is empty dictionary)
    datakitchen_url : str, optional
        DataKitchen platform URL (default is https://cloud.datakitchen.io)

    Raises
    ------
    HTTPError
        If the request fails.

    Returns
    ------
    requests.Response
        :class:`Response <Response>` object
    """
    order_create_url = f'{datakitchen_url}/v2/order/create/{kitchen}/{recipe}/{variation}'
    payload = {"schedule": "now", "parameters": parameters}
    response = requests.put(order_create_url, headers=headers, json=payload)
    response.raise_for_status()
    return response
