import asyncio
import os
import sys

import logging
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient

handler = logging.StreamHandler(stream=sys.stdout)
log_fmt = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(log_fmt)
logger = logging.getLogger('azure.eventhub')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
PUBLISH_EVENT_HUB_NAME = os.getenv("PUBLISH_EVENT_HUB_NAME")

async def run():
    # Create a producer client to send messages to the event hub.
    # Specify a connection string to your event hubs namespace and
    # the event hub name.
    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STR, eventhub_name=PUBLISH_EVENT_HUB_NAME
    )
    async with producer:
        # Create a batch.
        event_data_batch = await producer.create_batch()

        # Add events to the batch.
        event_data_batch.add(EventData("First event "))
        event_data_batch.add(EventData("Second event"))
        event_data_batch.add(EventData("Third event"))

        # Send the batch of events to the event hub.
        await producer.send_batch(event_data_batch)
        logger.info("Message sent successfully")

asyncio.run(run())