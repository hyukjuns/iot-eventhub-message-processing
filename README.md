# Eventhub Pub/Sub Application in Azure Kubernetes Service
- Eventhub Producer/Consumer Application 빌드 및 AKS 배포
- Prometheus, KEDA 를 사용한 Pub/Sub 모니터링 환경 구축
- Azure IoT SDK Sample Workload 를 사용한 부하 생성

## EventHub Pub/Sub Application

Path: [./python-apps/](./python-apps/)

EventHub Application / IoTHub Client Device / Kubernetes Manifests

![](./diagram/demo.svg)

## Monitoring and Scaling
## Kube Prometheus Stack & Managed Prometheus (Prometheus Agent Mode)

Path: [./Kubernetes_addons](./Kubernetes_addons)

Prometheus Agent 방식으로 Azure Monitor Workspace에 프로메테우스 메트릭을 Remote Write, 
즉, 한곳에서 멀티 클러스터의 데이터를 조회할 수 있음

![](./diagram/managed_prom.svg) 

## KEDA (EventHub Scaler)
Path: [./Kubernetes_addons](./Kubernetes_addons)

Eventhub의 처리되지 않은 메시지 수 기반 Pod 스케일링

![](./diagram/keda.svg)

## Opensource Eventhub Lag Monitoring
eventhub-custom-metrics-emitter

Path: [./eventhub-lag/](./eventhub-lag/)

- Eventhub Lag Value = Latest Offset - Current OFfset
- Azure Monitor 집계방식은 AVG 사용해야함 (Count는 메트릭 측정값이 몇개나 수집되었는지만 확인 하므로 측정값의 합인 Sum을 Count로 나눈 AVG 만 사용할 수 있음)

## Ref
- Storage Account Connection String Scheme

    ```bash
    DefaultEndpointsProtocol=https;AccountName=STORAGE;AccountKey=KEY
    ```

- [IotHub SDK Python](https://github.com/Azure/azure-iot-sdk-python)

- [IoTHub API Version Change logs](https://learn.microsoft.com/en-us/azure/templates/microsoft.devices/change-log/iothubs)