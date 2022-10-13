from __future__ import annotations

import logging
import os
import time

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from dkutils.constants import API_GET
from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient
from dkutils.decorators import retry_50X_httperror
from events_ingestion_client import (
    ApiClient,
    CloseRunApiSchema,
    Configuration,
    EventsApi,
    MessageLogEventApiSchema,
    TaskStatusApiSchema,
    TestReport,
    TestResultApiSchema,
)
from events_ingestion_client.rest import ApiException

logger = logging.getLogger(__name__)

DEFAULT_HOST = 'https://dev-api.datakitchen.io'
EVENT_SOURCE = 'API'

NODE_UNKNOWN = 'DKNodeStatus_Unknown'
NODE_TEMPLATE = 'DKNodeStatus_Template'
NODE_IN_CONFIGURATION = 'DKNodeStatus_in_configuration'
NODE_FULLY_CONFIGURED = 'DKNodeStatus_fully_configured'
NODE_NOT_RUN = 'DKNodeStatus_ready_for_production'
NODE_RUNNING = 'DKNodeStatus_in_production'
NODE_SUCCESSFULL = 'DKNodeStatus_completed_production'
NODE_FAILED = 'DKNodeStatus_production_error'
NODE_STOPPED = 'DKNodeStatus_production_stopped'
NODE_SKIPPED = 'DKNodeStatus_Skipped'

LOG_LEVELS_TO_REPORT = ['WARNING', 'ERROR', 'CRITICAL']
LOG_METADATA_KEYS_TO_REPORT = ['exc_desc', 'exc_type', 'traceback']
ALLOWED_TEST_STATUS_TYPES = ['PASSED', 'FAILED', 'WARNING']
TEST_SUITE = 'DataKitchen Tests'


@retry_50X_httperror()
def get_customer_code(dk_client: DataKitchenClient) -> str:
    """
    Retrieve the customer code from the authenticated user associated with the provided
    DataKitchen client.

    Parameters
    ----------
    dk_client: DataKitchenClient
        Client for making requests to the DataKitchen platform API.

    Returns
    -------
    str
        Customer code - typically two or three letters.
    """
    user_info = dk_client._api_request(API_GET, 'userinfo')
    return user_info.json()['customer_git_name']


def get_order_run_url(dk_client: DataKitchenClient, customer_code: str, order_run_id: str) -> str:
    """
    Retrieve the URL for navigating to the Order Run Details page in the DataKitchen platform for
    the provided order_run_id.

    Parameters
    ----------
    dk_client: DataKitchenClient
        Client for making requests to the DataKitchen platform API
    customer_code: str
        Customer code required for constructing the URL
    order_run_id
        Order run id the URL will link to
    Returns
    -------
    str
        URL for navigating to the Order Run Details page in the DataKitchen platform for the
        provided order_run_id.
    """
    base_url = dk_client._base_url
    kitchen = dk_client.kitchen
    return os.sep.join([base_url, '#', 'orders', customer_code, kitchen, 'runs', order_run_id])


@retry_50X_httperror()
def get_ingredient_owner_order_run_id(dk_client: DataKitchenClient):
    """
    If this order run is for an ingredient, then return the parent order run id. Otherwise, return
    None.

    Parameters
    ----------
    dk_client: DataKitchenClient
        Client for making requests to the DataKitchen platform API.

    Returns
    -------
    str or None
        Return the parent order run id if the current order run is for an ingredient, otherwise
        return None.
    """
    try:
        order_run_status = dk_client._api_request('get', 'order/status', dk_client.kitchen).json()

        # If this order run is for an ingredient, then it's in an ingredient kitchen with a single
        # order and order run and the status should contain an ingredient_owner_order_run field.
        return order_run_status['orders'][0]['input_settings']['ingredient_owner_order_run']
    except KeyError:
        return None


class TaskStatus(Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class EventInfoProvider:
    dk_client: DataKitchenClient
    customer_code: str
    pipeline_name: str
    order_run_id: str

    @classmethod
    def init(
            cls, dk_client: DataKitchenClient, pipeline_name: str, order_run_id: str
    ) -> EventInfoProvider:
        customer_code = get_customer_code(dk_client)
        return EventInfoProvider(dk_client, customer_code, pipeline_name, order_run_id)

    def get_event_info(self, **kwargs) -> dict:
        event_info = {'pipeline_name': self.pipeline_name, 'run_tag': self.order_run_id, **kwargs}

        if 'event_timestamp' not in event_info:
            event_info['event_timestamp'] = datetime.utcnow().isoformat()

        if 'external_url' not in event_info:
            event_info['external_url'] = get_order_run_url(
                self.dk_client, self.customer_code, self.order_run_id
            )

        return event_info


@dataclass
class Node:
    events_api_client: EventsApi
    event_info_provider: EventInfoProvider
    name: str
    info: dict = None
    started_event_published: bool = False
    status: str = None
    start_time: int = None
    end_time: int = None

    @property
    def running(self) -> bool:
        return self.status == NODE_RUNNING

    @property
    def succeeded(self) -> bool:
        return self.status == NODE_SUCCESSFULL

    @property
    def stopped(self) -> bool:
        return self.status == NODE_STOPPED

    @property
    def failed(self) -> bool:
        return self.status == NODE_FAILED

    def update(self, info: dict) -> None:
        self.info = info
        prev_status = self.status
        self.status = self.info['status']

        if prev_status != self.status:
            self._update_timings()
            self._handle_event()

        return self

    def _update_timings(self) -> None:
        start_time = self.info['start_time']
        timing = self.info['timing']

        if start_time:
            self.start_time = start_time
        elif self.start_time is None:
            self.start_time = int(time.time() * 1000)

        if timing:
            self.end_time = self.start_time + timing
        else:
            self.end_time = self.start_time

    def _handle_event(self) -> None:
        if self.running:
            self._publish_task_status_event(TaskStatus.STARTED, self.start_time)
            self.started_event_published = True
        elif self.succeeded or self.stopped:
            if not self.started_event_published:
                self._publish_task_status_event(TaskStatus.STARTED, self.start_time)
                self.started_event_published = True
            self._publish_task_status_event(TaskStatus.COMPLETED, self.end_time)
        elif self.failed:
            if not self.started_event_published:
                self._publish_task_status_event(TaskStatus.STARTED, self.start_time)
                self.started_event_published = True
            self._publish_task_status_event(TaskStatus.ERROR, self.end_time)

    def _publish_task_status_event(self, task_status: str, milliseconds_from_epoch: int) -> None:
        try:
            event_timestamp = datetime.utcfromtimestamp(milliseconds_from_epoch / 1000).isoformat()
            event_info = self.event_info_provider.get_event_info(
                task_name=self.name, task_status=task_status.name, event_timestamp=event_timestamp
            )
            logger.info(f'Publishing event: {event_info}')
            self.events_api_client.post_task_status(
                TaskStatusApiSchema(**event_info), event_source=EVENT_SOURCE
            )
        except ApiException as e:
            logger.error(f'Exception when calling EventsApi->post_task_status: {str(e)}\n')
            raise

    def publish_tests(self) -> None:
        test_reports = self._get_test_reports()

        if len(test_reports) == 0:
            return

        try:
            event_info = self.event_info_provider.get_event_info(
                task_name=self.name, test_results=test_reports, test_suite=TEST_SUITE
            )
            self.events_api_client.post_test_result(
                TestResultApiSchema(**event_info), event_source=EVENT_SOURCE
            )
        except ApiException as e:
            logger.error(f'Exception when calling EventsApi->post_test_result:: {str(e)}\n')

    def _extract_tests(self, tests: dict) -> list:
        test_reports = []
        for name, test in tests.items():
            status = test['status'].upper()
            if status in ALLOWED_TEST_STATUS_TYPES:
                test_reports.append(
                    TestReport(description=test['results'], name=name, status=status)
                )
        return test_reports

    def _get_test_reports(self) -> list:
        test_reports = []
        test_reports.extend(self._extract_tests(self.info['tests']))

        def add_reports(key):
            if key in self.info:
                for value in self.info[key].values():
                    test_reports.extend(self._extract_tests(value['tests']))

        [add_reports(key) for key in ['data_sources', 'data_sinks', 'actions']]

        return test_reports


class OrderRunMonitor:

    def __init__(
        self,
        dk_client: DataKitchenClient,
        events_api_key: str,
        pipeline_name: str,
        order_run_id: str,
        nodes_to_ignore: list = None,
        sleep_time_secs: int = 10,
        host: str = DEFAULT_HOST,
    ):
        """
        This class is for use in monitoring a DataKitchen Order Run and reporting its status to
        DataKitchen's Observability module Events Ingestion API. It will report the start/stop of
        each node as an individual task and close the run when finished.

        Parameters
        ----------
        dk_client : DataKitchenClient
        events_api_key : str
            Events Ingestion API key.
        pipeline_name : str
            Name of the pipeline being monitored
        order_run_id : str
            Id of the Order Run being monitored.
        nodes_to_ignore : list or None, optional
            List of nodes to ignore. If the monitor node is named Order_Run_Monitor, it is added to
            the ignore list by default and there is no need to add it here (default: None).
        sleep_time_secs : int, optional
            Polling interval for monitoring the run in seconds (default: 10).
        host : str, optional
            URL of the Events Ingestion API (default: https://dev-api.datakitchen.io').
        """
        self._dk_client = dk_client
        self.is_ingredient_order_run = False

        ingredient_owner_order_run_id = get_ingredient_owner_order_run_id(dk_client)
        if ingredient_owner_order_run_id is not None:
            logger.info(f'Ingredient order run originated from {ingredient_owner_order_run_id}')
            self.is_ingredient_order_run = True

        self._event_info_provider = EventInfoProvider.init(dk_client, pipeline_name, order_run_id)
        self._order_run_id = order_run_id
        self._nodes_to_ignore = nodes_to_ignore if nodes_to_ignore is not None else []
        self._nodes_to_ignore += ['Order_Run_Monitor']
        self._nodes_to_ignore += self.get_conditional_nodes()
        self._sleep_time_secs = sleep_time_secs

        # Configure API key authorization: SAKey
        configuration = Configuration()
        configuration.api_key['ServiceAccountAuthenticationKey'] = events_api_key
        configuration.host = host

        # Create an instance of the API class
        self._events_api_client = EventsApi(ApiClient(configuration))

    @retry_50X_httperror()
    def get_order_run_details(self, **kwargs) -> dict:
        """
        Retrieve order run details for the associated order run. The provided kwargs may be used to
        augment the returned value with more granular details.

        Parameters
        ----------
        kwargs
            Optional keyword arguments as found in DataKitchenClient's
            :func:`~dkutils.datakitchen_api.datakitchen_client.DataKitchenClient.get_order_run_details`

        Returns
        -------
        dict
            Dictionary of order run details
        """
        return self._dk_client.get_order_run_details(self._order_run_id, **kwargs)

    def get_conditional_nodes(self) -> list:
        """
        Retrieve a list of the conditional node names present in this Order Run.

        Returns
        -------
        list
            List of conditional node names.
        """
        order_run_details = self.get_order_run_details()
        return list(set([v['node'] for v in order_run_details.get('conditions', {}).values()]))

    def get_nodes_info(self) -> dict:
        """
        Extract and return the node information from the order run details, excluding the nodes that
        should be ignored (e.g. conditional nodes and the Order_Run_Monitor node itself).

        Returns
        -------
        dict
            Dictionary keyed by node name and valued by a dictionary of node details.
        """
        nodes_info = self.get_order_run_details(include_summary=True)['summary']['nodes']
        [nodes_info.pop(node_name, None) for node_name in self._nodes_to_ignore]
        return nodes_info

    def _create_node(self, name: str, info: dict) -> Node:
        """
        Create a Node object and initialize it.

        Parameters
        ----------
        name : str
            Node name
        info : dict
            Milliseconds from epoch when the node started executing

        Returns
        -------
        Node
        """
        return Node(self._events_api_client, self._event_info_provider, name).update(info)

    @staticmethod
    def parse_log_entry(log_entry: dict) -> dict:
        """
        Parse a log entry dictionary to derive the fields required for the
        MessageLogEventApiSchema.

        Parameters
        ----------
        log_entry : dict
            Dictionary of log details for a single log entry of the form::

                {
                    'datetime': '2022-08-16T14:38:58.611000',
                    'disk_used': '5.8984375 MB',
                    'exc_desc': None,
                    'exc_type': None,
                    'hostname': '0d4e31d0-1d9b-11ed-971d-621c363ef06a-lqq9t',
                    'mem_usage': '127.33 MB',
                    'message': 'Test Fail: DKDataTestFailed',
                    'node': 'Fail_Node',
                    'order_run_id': '115d3e42-1d9b-11ed-b495-c216e4cc8e61',
                    'pid': 22,
                    'priority': 27,
                    'record_type': 'ERROR',
                    'syslogts': '2022-08-16T14:38:58-05:00',
                    'thread_name': 'NodeExecutorThread:0',
                    'traceback': None
                }

        Returns
        -------
        dict
            Dictionary of required and optional fields for the MessageLogEventApiSchema
        """
        # Permitted log levels: "ERROR", "WARNING", and "INFO"
        log_level = log_entry['record_type'] if log_entry['record_type'] != 'CRITICAL' else 'ERROR'

        metadata = {}

        def add_metadata(key):
            if key in log_entry and log_entry[key] is not None:
                metadata[key] = log_entry[key]

        [add_metadata(k) for k in LOG_METADATA_KEYS_TO_REPORT]

        return {
            'event_timestamp': log_entry['syslogts'],
            'log_level': log_level,
            'message': log_entry['message'],
            'metadata': metadata,
            'task_name': log_entry['node']
        }

    def process_log_entries(self) -> None:
        """
        Send MessageLog events for WARNING and ERROR log messages.
        """
        try:
            for log_entry in self.get_order_run_details(include_logs=True)['log']['lines']:
                if log_entry['record_type'] in LOG_LEVELS_TO_REPORT and log_entry[
                        'node'] not in self._nodes_to_ignore:
                    try:
                        event_info = self._event_info_provider.get_event_info(
                            **self.parse_log_entry(log_entry)
                        )
                        body = MessageLogEventApiSchema(**event_info)
                        self._events_api_client.post_message_log(body, event_source=EVENT_SOURCE)
                    except ApiException as e:
                        logger.error(
                            f'Exception when calling EventsApi->post_message_log: {str(e)}'
                        )
        except Exception as e:
            logger.error(f'Failed to process logs: {str(e)}')

    def monitor(self) -> tuple:
        """
        Poll the DataKitchen platform API for the status of the associated Order Run. Report the
        status of each node until all the nodes have completed or if the run has failed and nodes
        stopped processing. If this order run is for an ingredient, monitoring is disabled.

        Returns
        -------
        tuple
            Contains two lists. The first list contains names of the nodes that succeeded, whereas
            the second list contains names of the nodes that failed. Both are empty if this is an
            ingredient order run.
        """
        if self.is_ingredient_order_run:
            logger.info('This is an ingredient order run - disabling monitoring.')
            return [], []

        nodes = []
        try:
            nodes_are_running = True
            nodes_info = self.get_nodes_info()
            nodes = [self._create_node(name, info) for name, info in nodes_info.items()]

            while nodes_are_running:
                # Update all the nodes with the latest run info
                [node.update(nodes_info[node.name]) for node in nodes]
                nodes_are_running = any([node.running for node in nodes])

                if nodes_are_running:
                    time.sleep(self._sleep_time_secs)
                    nodes_info = self.get_nodes_info()

            logger.info('Order run finished. Shutting Down...')
            successful_nodes = [node.name for node in nodes if node.succeeded]
            failed_nodes = [node.name for node in nodes if node.failed]
        finally:
            self.process_log_entries()
            [node.publish_tests() for node in nodes]
            self._events_api_client.post_close_run(
                CloseRunApiSchema(**self._event_info_provider.get_event_info())
            )

        return successful_nodes, failed_nodes
