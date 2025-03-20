import os
import sys
import asyncio
import logging
import time

from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore

# Application Insights (OpenTelemetry)
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import get_tracer
from opentelemetry.sdk.resources import Resource
from opencensus.ext.azure.log_exporter import AzureLogHandler

# 환경 변수 로드
BLOB_STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")  # 개별 Event Hub 엔티티
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP")
APPLICATION_INSIGHTS_CONNECTION_STRING = os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")

# 애플리케이션 이름 설정
resource = Resource.create({
    "service.name": "hyukjun-evt-receiver",
    "cloud.role": "hyukjun-evt-receiver"
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

async def on_event(partition_context, event):
    """Event Hub에서 메시지를 받을 때 실행되는 함수"""
    with tracer.start_as_current_span("eventhub.receive") as span:
        message = event.body_as_str(encoding="UTF-8")
        logger.info(f"Received event: {message}, from partition ID: {partition_context.partition_id}")

        # OpenTelemetry 속성 추가 (Event Hub 구독 관계가 Application Insights에 표시되도록 설정)
        span.set_attribute("messaging.system", "eventhub")  # 메시징 시스템을 Event Hub로 설정
        span.set_attribute("messaging.destination.name", EVENT_HUB_NAME)  # 개별 Event Hub 이름
        span.set_attribute("messaging.operation", "receive")  # Receive 작업
        span.set_attribute("eventhub.name", EVENT_HUB_NAME)  # Event Hub 이름
        span.set_attribute("partition.id", partition_context.partition_id)  # 파티션 정보
        span.set_attribute("cloud.roleInstance", "hyukjun-eventhub-instance")  # 애플리케이션 인스턴스 설정

        # 추가: Event Hub에서 메시지가 도착한 이벤트 기록
        span.add_event("Received message from Event Hub", {
            "eventhub.name": EVENT_HUB_NAME,
            "partition.id": partition_context.partition_id
        })

        # 체크포인트 업데이트
        await partition_context.update_checkpoint(event)

async def receive(client):
    """Event Hub에서 메시지를 수신"""
    await client.receive(
        on_event=on_event,
        starting_position="-1",  # "-1"은 파티션의 처음부터 시작
    )

async def main():
    """Event Hub에서 메시지 수신을 시작하는 메인 함수"""
    checkpoint_store = BlobCheckpointStore.from_connection_string(
        BLOB_STORAGE_CONNECTION_STRING, 
        BLOB_CONTAINER_NAME
    )

    client = EventHubConsumerClient.from_connection_string(
        EVENT_HUB_CONNECTION_STR,
        eventhub_name=EVENT_HUB_NAME,
        consumer_group=CONSUMER_GROUP,
        checkpoint_store=checkpoint_store
    )

    async with client:
        time.sleep(1)  # 서비스 시작 지연
        await receive(client)

if __name__ == "__main__":
    asyncio.run(main())
