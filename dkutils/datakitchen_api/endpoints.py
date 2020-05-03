import requests

from requests.exceptions import HTTPError

from dkutils.constants import DEFAULT_DATAKITCHEN_URL

# The servings API endpoint retrieves only 10 order runs by default. To retrieve them all, assume
# 100K exceeds the max order runs a given order will ever contain.
DEFAULT_SERVINGS_COUNT = 100000


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
    Create a new order.

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


def get_order_runs(headers, kitchen, order_id, datakitchen_url=DEFAULT_DATAKITCHEN_URL):
    """
    Retrieve all the order runs associated with the provided order.

    Parameters
    ----------
    headers : dict
        Headers containing authentication token.
    kitchen :  str
        Kitchen name
    order_id : str
        Order id for which to retrieve order runs
    datakitchen_url : str, optional
        DataKitchen platform URL (default is https://cloud.datakitchen.io)

    Returns
    ------
    list or None
        None if no order runs are found. Otherwise, return a list of order run details. Each order
        run details entry is of the form::

            {
                "order_id": "71d8a966-38e0-11ea-8cf9-a6bbea194887",
                "status": "COMPLETED_SERVING",
                "orderrun_status": "OrderRun Completed",
                "hid": "a8978ddc-83c7-11ea-88ba-9a815c325cee",
                "variation_name": "dk_agent_checker_run_hourly",
                "timings": {
                  "start-time": 1587470413845,
                  "end-time": 1587470432441,
                  "duration": 18596
                }
            }

    """
    try:
        order_status_url = f'{datakitchen_url}/v2/order/servings/{kitchen}/{order_id}'
        payload = {'count': DEFAULT_SERVINGS_COUNT}
        response = requests.get(order_status_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['servings']
    except HTTPError:
        print(f'No order runs found for provided order id ({order_id}) in kitchen {kitchen}')


def get_order_run_details(headers, kitchen, order_run_id, datakitchen_url=DEFAULT_DATAKITCHEN_URL):
    """
    Retrieve the details of an order run.

    Parameters
    ----------
    headers : dict
        Headers containing authentication token.
    kitchen :  str
        Kitchen name
    order_run_id : str
        Order run id for which to retrieve details
    datakitchen_url : str, optional
        DataKitchen platform URL (default is https://cloud.datakitchen.io)

    Raises
    ------
    HTTPError
        If the request fails.

    Returns
    ------
    dict
        Order run details of the form::

            {
                "order_id": "ca789c92-8bb6-11ea-883f-46ee3c6afcbf",
                "hid": "cd463d80-8bb6-11ea-97c5-8a10ccb96113",
                "recipe_id": "ce7b696e-8bb6-11ea-97c5-8a10ccb96113",
                "status": "SERVING_ERROR",
                "variation_name": "sub_workflow",
                "recipe_name": "Sub_Workflow",
                "run_time_variables": {
                    "CAT": "CLS",
                    "CurrentKitchen": "Add_Real_Data_and_Infrastructure",
                    "CurrentOrderId": "ca789c92-8bb6-11ea-883f-46ee3c6afcbf",
                    "CurrentOrderRunId": "cd463d80-8bb6-11ea-97c5-8a10ccb96113",
                    "CurrentVariation": "sub_workflow",
                    "DH": "12",
                    "DT": "20200426",
                    ...
                    ...
                    ...
                    "tableauConfig": {
                        "username": "",
                        "password": "",
                        "url_login": "",
                        "url": "",
                        "selenium_url": "",
                        "content_url": ""
                    }
                },
                "orderrun_status": "Error in OrderRun",
                "resumed_by": null,
                "scheduled_start_time": 1588342778543,
                "variation": {},
                "state": "unknown DKNodeStatus"
            }

    """
    order_run_details_url = f'{datakitchen_url}/v2/order/details/{kitchen}'
    payload = {
        'logs': False,
        'serving_hid': f'{order_run_id}',
        'servingjson': False,
        'summary': False,
        'testresults': False,
        'timingresults': False
    }
    response = requests.post(order_run_details_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['servings'][0]
