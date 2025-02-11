import os,sys
import asyncio
import logging
import time

from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import (
    BlobCheckpointStore,
)

BLOB_STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP")

handler = logging.StreamHandler(stream=sys.stdout)
log_fmt = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(log_fmt)
logger = logging.getLogger('azure.eventhub')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

logger = logging.getLogger("azure.eventhub")
logging.basicConfig(level=logging.INFO)

async def on_event(partition_context, event):

    message = event.body_as_str(encoding="UTF-8")
    logger.info(f"Received event: {message}, from partition ID: {partition_context.partition_id}")
    await partition_context.update_checkpoint(event)

async def receive(client):
    await client.receive(
        on_event=on_event,
        starting_position="-1",  # "-1" is from the beginning of the partition.
    )

async def main():
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
        time.sleep(1)
        await receive(client)
        
if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    asyncio.run(main())