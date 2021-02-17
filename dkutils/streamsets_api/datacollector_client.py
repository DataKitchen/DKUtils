from enum import Enum

import requests

from dkutils.constants import (API_GET, API_POST)


class PipelineStatus(Enum):
    EDITED = 'EDITED'  # The pipeline has been created or modified, and has not run since the last modification.
    FINISHED = 'FINISHED'  # The pipeline has completed all expected processing and has stopped running.
    RUN_ERROR = 'RUN_ERROR'  # The pipeline encountered an error while running and stopped.
    RUNNING = 'RUNNING'  # The pipeline is running.
    STOPPED = 'STOPPED'  # The pipeline was manually stopped.
    START_ERROR = 'START_ERROR'  # The pipeline encountered an error while starting and failed to start.
    STOP_ERROR = 'STOP_ERROR'  # The pipeline encountered an error while stopping.
    CONNECT_ERROR = 'CONNECT_ERROR'  # noqa: When running a cluster-mode pipeline, Data Collector cannot connect to the underlying cluster manager, such as Mesos or YARN.
    CONNECTING = 'CONNECTING'  # The pipeline is preparing to restart after a Data Collector restart.
    DISCONNECTED = 'DISCONNECTED'  # noqa: The pipeline is disconnected from external systems, typically because Data Collector is restarting or shutting down.
    FINISHING = 'FINISHING'  # The pipeline is in the process of finishing all expected processing.
    RETRY = 'RETRY'  # noqa: The pipeline is trying to run after encountering an error while running. This occurs only when the pipeline is configured for a retry upon error.
    RUNNING_ERROR = 'RUNNING_ERROR'  # The pipeline encounters errors while running.
    STARTING = 'STARTING'  # The pipeline is initializing, but hasn't started yet.
    STARTING_ERROR = 'STARTING_ERROR'  # The pipeline encounters errors while starting.
    STOPPING = 'STOPPING'  # The pipeline is in the process of stopping after a manual request to stop.
    STOPPING_ERROR = 'STOPPING_ERROR'  # The pipeline encounters errors while stopping.


class DataCollectorClient:

    def __init__(self, host, port, username, password):
        """
        Client object for invoking `StreamSets Data Collector
        REST API <https://streamsets.com/blog/retrieving-metrics-via-streamsets-data-collector-rest-api/>`_

        Parameters
        ----------
        host: str
          The name of the host to use in making REST API calls.
        port: int
          The port to use in making REST API calls.
        username : str
          Username to authenticate when making REST API calls.
        password : str
          Password to authenticate when making REST API calls.

        """
        self._base_url = f'http://{host}:{port}/rest/v1/'
        self._auth = (username, password)

    def _validate_pipline_id(self, pipeline_id):
        """Ensure that the pipeline_id is given"""
        if not pipeline_id:
            raise ValueError('pipeline_id is required')

    def _api_request(self, http_method, *args, **kwargs):
        """
        Make HTTP request to arbitrary API endpoint, with optional parameters as payload.

        Parameters
        ----------
        http_method : str
            HTTP method to use when making API request.
        *args : list
            Variable length list of strings to construct endpoint path.
        **kwargs : dict
            Arbitrary keyword arguments to construct request payload.

        Raises
        ------
        HTTPError
            If the request fails.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object
        """
        api_request = getattr(requests, http_method)
        api_path = f'{self._base_url}{"/".join(args)}'
        response = api_request(
            api_path, auth=self._auth, headers={'X-Requested-By': 'DataKitchen'}, json=kwargs
        )
        response.raise_for_status()
        return response

    def _pipeline_operation(self, http_method, pipeline_id, operation, **kwargs):
        """
        This is an internal function that is used to invoke a pipeline operation which returns the pipeline status

        Parameters
        ----------
        http_method : str
            HTTP method to use when making API request.
        pipeline_id: str
            The pipeline id of the pipeline for which status information is being requested
        operation: str
            The pipeline operation to be performed
        **kwargs : dict
            Arbitrary keyword arguments to construct runtime parameters

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the pipeline_id is None

        Returns
        -------
        requests.Response.json()
        """
        self._validate_pipline_id(pipeline_id)
        return self._api_request(
            http_method, 'pipeline', pipeline_id, f'{operation}?rev=0', **kwargs
        ).json()

    def get_pipeline_full_status(self, pipeline_id):
        """
        Get the JSON containing the status of the pipeline with the given pipeline_id

        Parameters
        ----------
        pipeline_id: str
            The pipeline id of the pipeline for which status information is being requested

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the pipeline_id is None

        Returns
        -------
        requests.Response.json()
        """
        return self._pipeline_operation(API_GET, pipeline_id, 'status')

    def get_pipeline_status(self, pipeline_id):
        """
        Get an instance of Pipeline.Status that represents the status of the pipeline with the given pipeline_id

        Parameters
        ----------
        pipeline_id: str
            The pipeline id of the pipeline for which status information is being requested

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the pipeline_id is None

        Returns
        -------
        PipelineStatus
            :class:`PipelineStatus <PipelineStatus>` object
        """
        status = self.get_pipeline_full_status(pipeline_id)['status']
        return PipelineStatus(status)

    def start_pipeline(self, pipeline_id, **kwargs):
        """
        Start the pipeline with the given pipeline_id

        Parameters
        ----------
        pipeline_id: str
            The pipeline id of the pipeline to start
        **kwargs : dict
            Arbitrary keyword arguments to construct runtime parameters

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the pipeline_id is None

        Returns
        -------
        requests.Response.json()
        """
        return self._pipeline_operation(API_POST, pipeline_id, 'start', **kwargs)

    def stop_pipeline(self, pipeline_id, **kwargs):
        """
        Stop the pipeline with the given pipeline_id

        Parameters
        ----------
        pipeline_id: str
            The pipeline id of the pipeline to stop
        **kwargs : dict
            Arbitrary keyword arguments to construct runtime parameters

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the pipeline_id is None

        Returns
        -------
        requests.Response.json()
        """
        return self._pipeline_operation(API_POST, pipeline_id, 'stop', **kwargs)

    def reset_pipeline(self, pipeline_id):
        """
        Resets the origin offset of the pipeline with the given pipeline_id

        Parameters
        ----------
        pipeline_id: str
            The pipeline id of the pipeline for which status information is being requested

        Raises
        ------
        HTTPError
            If the request fails.
        ValueError
            If the pipeline_id is None
        """
        self._validate_pipline_id(pipeline_id)
        self._api_request(API_POST, 'pipeline', pipeline_id, 'resetOffset?rev=0')
