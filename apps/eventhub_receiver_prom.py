import os
import asyncio
import logging

# Prometheus Lib
from prometheus_client import Counter, Gauge, start_http_server

from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import (
    BlobCheckpointStore,
)

BLOB_STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP")

logger = logging.getLogger("azure.eventhub")
logging.basicConfig(level=logging.INFO)

# Prometheus Metrics 초기화
event_processing_rate = Counter('eventhub_processed_events_total', 'Total number of events processed')
event_processing_rate_per_second = Gauge('eventhub_processing_rate', 'Number of events processed per second')

# 초당 이벤트 처리 계산을 위한 상태
processed_events = 0

async def on_event(partition_context, event):
    
    global processed_events

    # Prometheus Counter 증가
    event_processing_rate.inc()

    logger.info(
        'Received the event: "{}" from the partition with ID: "{}"'.format(
            event.body_as_str(encoding="UTF-8"), partition_context.partition_id
        )
    )

    processed_events += 1
    await partition_context.update_checkpoint(event)

async def track_processing_rate():
    """초당 처리량 계산."""
    global processed_events

    while True:
        event_processing_rate_per_second.set(processed_events)
        processed_events = 0
        await asyncio.sleep(1)  # 초당 계산

async def receive(client):
    await client.receive(
        on_event=on_event,
        starting_position="-1",  # "-1" is from the beginning of the partition.
    )

async def main():
    
    start_http_server(8000)  # Prometheus에서 메트릭 수집 가능

    # Create an Azure blob checkpoint store to store the checkpoints.
    checkpoint_store = BlobCheckpointStore.from_connection_string(
        BLOB_STORAGE_CONNECTION_STRING, 
        BLOB_CONTAINER_NAME
    )

    # Create a consumer client for the event hub.
    client = EventHubConsumerClient.from_connection_string(
        EVENT_HUB_CONNECTION_STR,
        eventhub_name=EVENT_HUB_NAME,
        consumer_group=CONSUMER_GROUP,
        checkpoint_store=checkpoint_store
    )
    async with client:
        await asyncio.gather(receive(client), track_processing_rate())
        
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())