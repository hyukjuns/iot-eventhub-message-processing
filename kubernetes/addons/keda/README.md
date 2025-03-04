# KEDA with Azure Eventhub
1. Install keda by helm

https://keda.sh/docs/2.14/deploy/#helm

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
```

2. 이벤트허브 스케일러 구성

https://keda.sh/docs/2.16/scalers/azure-event-hub/#trigger-specification

> Manifest >> [scaledobjecy.yaml](./scaledobject.yaml)

3. 프로메테우스 연결 (서비스모니터)

```yaml
# user-vaules.yaml
prometheus:
  metricServer:
    enabled: true
    serviceMonitor:
      # -- Enables ServiceMonitor creation for the Prometheus Operator
      enabled: true
  operator:
    enabled: true
    serviceMonitor:
      # -- Enables ServiceMonitor creation for the Prometheus Operator
      enabled: true
  webhooks:
    enabled: true
    serviceMonitor:
      enabled: true
```
