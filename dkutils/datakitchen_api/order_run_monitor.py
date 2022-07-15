from __future__ import print_function

import logging
import time

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from dkutils.datakitchen_api.datakitchen_client import DataKitchenClient
from dkutils.decorators import retry_50X_httperror
from events_ingestion_client import (
    ApiClient,
    CloseRunSchemaRequestBody,
    Configuration,
    EventsApi,
    TaskStatusSchemaRequestBody,
)
from events_ingestion_client.rest import ApiException

logger = logging.getLogger(__name__)

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


class TaskStatus(Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class EventInfoProvider:
    pipeline_name: str

    def get_event_info(self, **kwargs):
        return {
            "pipeline_name": self.pipeline_name,
            "event_timestamp": datetime.now().isoformat(),
            **kwargs
        }


@dataclass
class Node:
    events_api_client: EventsApi
    event_info_provider: EventInfoProvider
    name: str
    status: str

    @property
    def running(self):
        return self.status == NODE_RUNNING

    @property
    def succeeded(self):
        return self.status == NODE_SUCCESSFULL

    @property
    def stopped(self):
        return self.status == NODE_STOPPED

    @property
    def failed(self):
        return self.status == NODE_FAILED

    def init(self):
        self._handle_event()
        return self

    def update(self, nodes_info: dict):
        new_status = nodes_info[self.name]['status']
        if self.status != new_status:
            self.status = new_status
            self._handle_event()

    def _handle_event(self):
        if self.running:
            self._publish_task_status_event(TaskStatus.STARTED)
        elif self.succeeded or self.stopped:
            self._publish_task_status_event(TaskStatus.COMPLETED)
        elif self.failed:
            self._publish_task_status_event(TaskStatus.ERROR)

    def _publish_task_status_event(self, task_status: str):
        try:
            event_info = self.event_info_provider.get_event_info(
                task_name=self.name, task_status=task_status.name
            )
            logger.info(f"Publishing event: {event_info}")
            self.events_api_client.post_task_status(
                TaskStatusSchemaRequestBody(**event_info), event_source='API'
            )
        except ApiException as e:
            logger.error("Exception when calling EventsApi->post_task_status: %s\n" % e)
            raise


class OrderRunMonitor:

    def __init__(
        self,
        dk_client: DataKitchenClient,
        events_api_key: str,
        pipeline_name: str,
        order_run_id: str,
        nodes_to_ignore: list = None,
        sleep_time_secs: int = 10
    ):
        self._dk_client = dk_client
        self._event_info_provider = EventInfoProvider(pipeline_name)
        self._order_run_id = order_run_id
        self._nodes_to_ignore = nodes_to_ignore if nodes_to_ignore is not None else []
        self._nodes_to_ignore += ['Monitor_and_Publish_Order_Run_Events']
        self._nodes_to_ignore += self.get_conditional_nodes()
        self._sleep_time_secs = sleep_time_secs

        # Configure API key authorization: SAKey
        configuration = Configuration()
        configuration.api_key['ServiceAccountAuthenticationKey'] = events_api_key

        # Create an instance of the API class
        self._events_api_client = EventsApi(ApiClient(configuration))

    @retry_50X_httperror()
    def get_order_run_details(self):
        return self._dk_client.get_order_run_details(self._order_run_id, include_summary=True)

    def get_conditional_nodes(self):
        order_run_details = self.get_order_run_details()
        return list(set([v['node'] for v in order_run_details.get('conditions', {}).values()]))

    def get_nodes_info(self):
        nodes_info = self.get_order_run_details()['summary']['nodes']
        [nodes_info.pop(node_name, None) for node_name in self._nodes_to_ignore]
        return nodes_info

    def monitor(self):
        try:
            nodes_are_running = True
            nodes_info = self.get_nodes_info()
            nodes = [
                Node(self._events_api_client, self._event_info_provider, name,
                     info['status']).init() for name, info in nodes_info.items()
            ]

            while nodes_are_running:
                # Update all the nodes with the latest run info
                [node.update(nodes_info) for node in nodes]
                nodes_are_running = any([node.running for node in nodes])

                if nodes_are_running:
                    time.sleep(self._sleep_time_secs)
                    nodes_info = self.get_nodes_info()

            logger.info('Order run finished. Shutting Down...')
            successful_nodes = [node.name for node in nodes if node.succeeded]
            failed_nodes = [node.name for node in nodes if node.failed]
        finally:
            self._events_api_client.post_close_run(
                CloseRunSchemaRequestBody(**self._event_info_provider.get_event_info())
            )

        return successful_nodes, failed_nodes
