from enum import Enum

import requests

from dkutils.constants import (
    API_GET
)


class PipelineStatus(Enum):
    EDITED = 'EDITED'  # The pipeline has been created or modified, and has not run since the last modification.
    FINISHED = 'FINISHED'  # The pipeline has completed all expected processing and has stopped running.
    RUN_ERROR = 'RUN_ERROR'  # The pipeline encountered an error while running and stopped.
    RUNNING = 'RUNNING'  # The pipeline is running.
    STOPPED = 'STOPPED'  # The pipeline was manually stopped.
    START_ERROR = 'START_ERROR'  # The pipeline encountered an error while starting and failed to start.
    STOP_ERROR = 'STOP_ERROR'  # The pipeline encountered an error while stopping.
    CONNECT_ERROR = 'CONNECT_ERROR'  # When running a cluster-mode pipeline, Data Collector cannot connect to the underlying cluster manager, such as Mesos or YARN.
    CONNECTING = 'CONNECTING'  # The pipeline is preparing to restart after a Data Collector restart.
    DISCONNECTED = 'DISCONNECTED'  # The pipeline is disconnected from external systems, typically because Data Collector is restarting or shutting down.
    FINISHING = 'FINISHING'  # The pipeline is in the process of finishing all expected processing.
    RETRY = 'RETRY'  # The pipeline is trying to run after encountering an error while running. This occurs only when the pipeline is configured for a retry upon error.
    RUNNING_ERROR = 'RUNNING_ERROR'  # The pipeline encounters errors while running.
    STARTING = 'STARTING'  # The pipeline is initializing, but hasn't started yet.
    STARTING_ERROR = 'STARTING_ERROR'  # The pipeline encounters errors while starting.
    STOPPING = 'STOPPING'  # The pipeline is in the process of stopping after a manual request to stop.
    STOPPING_ERROR = 'STOPPING_ERROR'  # The pipeline encounters errors while stopping.


class StreamSetsDataCollectorClient:

    def __init__(
            self, host, port, username, password
    ):
        """
                Client object for invoking `StreamSets Data Collector REST API<https://streamsets.com/blog/retrieving-metrics-via-streamsets-data-collector-rest-api/>'

                Parameters
                ----------
                host: str
                  The name of the to use in making REST API calls.
                port: int
                  The port to use in making REST API calls.
                username : str
                  Username to authenticate when making REST API calls.
                password : str
                  Password to authenticate when making REST API calls.

                """
        self._base_url = f'http://{host}:{port}/rest/v1/'
        self._auth = (username, password)

    def _api_request(self, http_method, *args, is_json=True, **kwargs):
        """
        Make HTTP request to arbitrary API endpoint, with optional parameters as payload.

        Parameters
        ----------
        http_method : str
            HTTP method to use when making API request.
        *args : list
            Variable length list of strings to construct endpoint path.
        is_json : bool
            Set to False if payload/response is not JSON data.
        **kwargs : dict
            Arbitrary keyword arguments to construct request payload.

        Returns
        -------
        requests.Response
            :class:`Response <Response>` object
        """
        api_request = getattr(requests, http_method)
        api_path = f'{self._base_url}{"/".join(args)}'
        if is_json:
            response = api_request(api_path, auth=self._auth, json=kwargs)
        else:
            response = api_request(api_path, auth=self._auth, data=kwargs)
        response.raise_for_status()
        return response

    def get_pipeline_full_status(self, pipeline_id):
        """
        Get the JSON containing the status of the pipeline with the given pipeline_id

        Parameters
        ----------
        pipeline_id: str
            The pipeline id of the pipeline for which status information is being requested

        Returns
        -------
        requests.Response.json()
        """
        if not pipeline_id:
            raise ValueError(f'pipeline_id is required')
        return self._api_request(API_GET, 'pipeline', pipeline_id, 'status?rev=0').json()

    def get_pipeline_status(self, pipeline_id):
        """
                Get an instacne of Pipeline.Status that represents the status of the pipeline with the given pipeline_id

                Parameters
                ----------
                pipeline_id: str
                    The pipeline id of the pipeline for which status information is being requested

                Returns
                -------
                PipelineStatus
                    :class:`PipelineStatus <PipelineStatus>` object
                """
        status = self.get_pipeline_full_status(pipeline_id)['status']
        return PipelineStatus(status)
