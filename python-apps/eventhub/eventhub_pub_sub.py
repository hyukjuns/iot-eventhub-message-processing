import os
import sys
import asyncio
import logging

# Prometheus Lib
from prometheus_client import Counter, Gauge, start_http_server

from azure.eventhub.aio import EventHubProducerClient, EventHubConsumerClient
from azure.eventhub import EventData
from azure.eventhub.extensions.checkpointstoreblobaio import (
    BlobCheckpointStore,
)

BLOB_STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP")
PUBLISH_EVENT_HUB_NAME = os.getenv("PUBLISH_EVENT_HUB_NAME")

handler = logging.StreamHandler(stream=sys.stdout)
log_fmt = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(log_fmt)
logger = logging.getLogger('azure.eventhub')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Prometheus Metrics 초기화
event_processed_total = Counter('eventhub_processed_events_total', 'Total number of events processed')

async def send_message(producer_client, processed_dummy_message):
    """Receive된 메시지를 Event Hub로 발행."""
    try:
        event_data_batch = await producer_client.create_batch()
        event_data_batch.add(EventData(processed_dummy_message))
        await producer_client.send_batch(event_data_batch)
        logger.info("Message sent successfully: %s", processed_dummy_message)
    except ValueError:
        logger.error("Message too large to send: %s", processed_dummy_message)
    except Exception as e:
        logger.error("Error sending message: %s", str(e))

async def process_event(producer_client, partition_context, event):
    """Receive한 이벤트를 처리하고 발송 준비."""
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            message = event.body_as_str(encoding="UTF-8")
            # 송신메세지 만들기기
            processed_dummy_message = f"processed_dummy_message - {message}"
            logger.info(f"Received event: {message}, from partition ID: {partition_context.partition_id}")
            # 메시지 전송 호출
            await send_message(producer_client, processed_dummy_message)
            # 체크포인트 업데이트
            await partition_context.update_checkpoint(event)
            # Prometheus 메트릭 업데이트
            event_processed_total.inc()
            logger.info("Event processed and checkpoint updated.")
            break
        except Exception as e:
            retry_count += 1
            logger.error("Error processing event: %s", str(e))
            if retry_count == max_retries:
                logger.error("Failed to process event after %d retries", max_retries)

async def receive_messages(producer_client):
    """Event Hub에서 메시지를 수신."""
    logger.info("Starting to receive messages from Event Hub.")
    # Create an Azure blob checkpoint store to store the checkpoints.
    checkpoint_store = BlobCheckpointStore.from_connection_string(
        BLOB_STORAGE_CONNECTION_STRING, 
        BLOB_CONTAINER_NAME
    )

    # Create a consumer client for the event hub.
    consumer_client = EventHubConsumerClient.from_connection_string(
        EVENT_HUB_CONNECTION_STR,
        eventhub_name=EVENT_HUB_NAME,
        consumer_group=CONSUMER_GROUP,
        checkpoint_store=checkpoint_store
    )

    async with consumer_client:
        await consumer_client.receive(
            on_event=lambda partition_context, event: process_event(producer_client, partition_context, event),
            starting_position="-1"  # "-1" is from the beginning of the partition.
        )

async def main():
    start_http_server(8000)  # Prometheus에서 메트릭 수집 가능
    logger.info("Prometheus HTTP server started on port 8000.")

    producer_client = EventHubProducerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STR,
        eventhub_name=PUBLISH_EVENT_HUB_NAME
    )
    async with producer_client:
        await receive_messages(producer_client)

if __name__ == "__main__":
    asyncio.run(main())
