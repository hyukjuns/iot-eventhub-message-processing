import os
import sys
import asyncio
import logging

# Azure Event Hub
from azure.eventhub.aio import EventHubProducerClient, EventHubConsumerClient
from azure.eventhub import EventData
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore

# Application Insights (OpenTelemetry)
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import get_tracer, Link
from opentelemetry.sdk.resources import Resource
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opentelemetry.propagate import extract, inject
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# 환경 변수 로드
BLOB_STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_A_NAME = os.getenv("EVENT_HUB_NAME")  # Event Hub A (구독)
EVENT_HUB_B_NAME = os.getenv("PUBLISH_EVENT_HUB_NAME")  # Event Hub B (발행)
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP")
APPLICATION_INSIGHTS_CONNECTION_STRING = os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")

# 애플리케이션 이름 설정
resource = Resource.create({
    "service.name": "hyukjun-consumer-producer",
    "cloud.role": "hyukjun-consumer-producer",
    "cloud.roleInstance": "hyukjun-consumer-producer-instance"
})

# Application Insights 설정
configure_azure_monitor(connection_string=APPLICATION_INSIGHTS_CONNECTION_STRING, resource=resource)

# Logger 설정
logger = logging.getLogger("azure.eventhub")
logger.setLevel(logging.INFO)

# Application Insights 로그 핸들러 추가
logger.addHandler(AzureLogHandler(connection_string=APPLICATION_INSIGHTS_CONNECTION_STRING))

# OpenTelemetry 트레이서 설정
tracer = get_tracer(__name__)

async def send_message(producer_client, processed_dummy_message, parent_span):
    """Receive된 메시지를 Event Hub B로 발행"""
    with tracer.start_as_current_span("eventhub.send", parent=parent_span) as span:
        try:
            # 트레이스 컨텍스트를 메시지 속성에 추가
            trace_context = {}
            TraceContextTextMapPropagator().inject(trace_context)

            event_data_batch = await producer_client.create_batch()
            event_data = EventData(processed_dummy_message)
            event_data.properties = trace_context  # 트레이스 컨텍스트 포함
            event_data_batch.add(event_data)

            await producer_client.send_batch(event_data_batch)
            logger.info("Message sent successfully to Event Hub B: %s", processed_dummy_message)

            # OpenTelemetry 속성 추가 (Event Hub B로 메시지 전송)
            span.set_attribute("messaging.system", "eventhub")
            span.set_attribute("messaging.destination.name", EVENT_HUB_B_NAME)  # 개별 Event Hub B로 구분
            span.set_attribute("messaging.operation", "send")
            span.set_attribute("eventhub.name", EVENT_HUB_B_NAME)

        except ValueError:
            logger.error("Message too large to send: %s", processed_dummy_message)
        except Exception as e:
            logger.error("Error sending message: %s", str(e))

async def process_event(producer_client, partition_context, event, parent_span):
    """Receive한 이벤트를 처리하고 발송 준비"""
    context = extract(event.properties)
    span_link = Link(context)

    with tracer.start_as_current_span("eventhub.process", parent=parent_span, links=[span_link]) as span:
        try:
            message = event.body_as_str(encoding="UTF-8")
            processed_dummy_message = f"processed_dummy_message - {message}"
            logger.info(f"Received event from Event Hub A: {message}, from partition ID: {partition_context.partition_id}")

            # OpenTelemetry 속성 추가 (이벤트 처리 중임을 명확히 표현)
            span.set_attribute("eventhub.name", EVENT_HUB_A_NAME)
            span.set_attribute("partition.id", partition_context.partition_id)
            span.set_attribute("messaging.system", "eventhub")
            span.set_attribute("messaging.destination.name", EVENT_HUB_A_NAME)
            span.set_attribute("messaging.operation", "process")

            # 메시지 전송 호출 (Event Hub B로 메시지 전송)
            await send_message(producer_client, processed_dummy_message, span)

            # 체크포인트 업데이트
            await partition_context.update_checkpoint(event)

            logger.info("Event processed and checkpoint updated.")
        except Exception as e:
            logger.error("Error processing event: %s", str(e))

async def receive_messages(producer_client):
    """Event Hub A에서 메시지를 수신"""
    logger.info("Starting to receive messages from Event Hub A.")

    checkpoint_store = BlobCheckpointStore.from_connection_string(
        BLOB_STORAGE_CONNECTION_STRING, 
        BLOB_CONTAINER_NAME
    )

    consumer_client = EventHubConsumerClient.from_connection_string(
        EVENT_HUB_CONNECTION_STR,
        eventhub_name=EVENT_HUB_A_NAME,
        consumer_group=CONSUMER_GROUP,
        checkpoint_store=checkpoint_store
    )

    async def on_event(partition_context, event):
        """이벤트 수신 시 호출되는 함수"""
        context = extract(event.properties)

        with tracer.start_as_current_span("eventhub.receive", links=[Link(context)]) as receive_span:
            logger.info(f"Received message from Event Hub A: {event.body_as_str(encoding='UTF-8')}")
            await process_event(producer_client, partition_context, event, receive_span)

    async with consumer_client:
        await consumer_client.receive(
            on_event=on_event,
            starting_position="-1"
        )

async def main():
    producer_client = EventHubProducerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STR,
        eventhub_name=EVENT_HUB_B_NAME
    )
    async with producer_client:
        await receive_messages(producer_client)

if __name__ == "__main__":
    asyncio.run(main())
