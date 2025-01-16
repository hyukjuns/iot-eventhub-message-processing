import os
import sys
import asyncio
import logging
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
from pymongo import MongoClient

# 환경 변수 설정
BLOB_STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP")
COSMOS_DB_CONNECTION_STRING = os.getenv("COSMOS_DB_CONNECTION_STRING")
COSMOS_DB_DATABASE_NAME = os.getenv("COSMOS_DB_DATABASE_NAME")
COSMOS_DB_COLLECTION_NAME = os.getenv("COSMOS_DB_COLLECTION_NAME")

# 로깅 설정
handler = logging.StreamHandler(stream=sys.stdout)
log_fmt = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(log_fmt)
logger = logging.getLogger("azure.eventhub")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Cosmos DB 클라이언트 생성
cosmos_client = MongoClient(COSMOS_DB_CONNECTION_STRING)
db = cosmos_client[COSMOS_DB_DATABASE_NAME]
collection = db[COSMOS_DB_COLLECTION_NAME]

async def save_to_cosmosdb(data):
    """Cosmos DB에 데이터를 저장."""
    try:
        result = collection.insert_one(data)
        logger.info(f"Data saved to Cosmos DB with ID: {result.inserted_id}")
    except Exception as e:
        logger.error(f"Error saving data to Cosmos DB: {str(e)}")

async def process_event(partition_context, event):
    """Receive한 이벤트를 처리하고 Cosmos DB에 저장."""
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            message = event.body_as_str(encoding="UTF-8")
            logger.info(f"Received event: {message}, from partition ID: {partition_context.partition_id}")

            # 데이터 처리
            processed_data = {
                "original_message": message,
                "partition_id": partition_context.partition_id
            }

            # Cosmos DB에 저장
            await save_to_cosmosdb(processed_data)

            # 체크포인트 업데이트
            await partition_context.update_checkpoint(event)

            logger.info("Event processed and checkpoint updated.")
            break
        except Exception as e:
            retry_count += 1
            logger.error("Error processing event: %s", str(e))
            if retry_count == max_retries:
                logger.error("Failed to process event after %d retries", max_retries)

async def receive_messages():
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
            on_event=process_event,
            starting_position="-1"  # "-1" is from the beginning of the partition.
        )

async def main():
    await receive_messages()

if __name__ == "__main__":
    asyncio.run(main())