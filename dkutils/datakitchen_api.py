import requests


DEFAULT_DATAKITCHEN_URL = 'https://cloud.datakitchen.io'


def get_headers(username, password, datakitchen_url=DEFAULT_DATAKITCHEN_URL):
    """
    Login to the DataKitchen platform via the login API to retreive a token. Store the \
    token in headers required to make subsequent API requests.

    Parameters
    ----------
    username : str
      DataKitchen platform username.
    password : str
      DataKitchen platform password.
    datakitchen_url : str
      DataKitchen platform url.

    Raises
    ------
    HTTPError
        If the request fails.

    Returns
    -------
    dict
        Dictionary required by subsequent API requests
    """
    credentials = dict()
    credentials['username'] = username
    credentials['password'] = password

    login_url = f'{datakitchen_url}/v2/login'
    response = requests.post(login_url, data=credentials)
    response.raise_for_status()
    return {'Authorization': f'Bearer {response.text}'}

