## 물리 및 논리적 자원 격리
모니터링을 위한 Prometheus Stack 및 KEDA Addon Application 배포 시 기존 워크로드와 물리/논리적으로 격리된 환경에 배포하기 위함

### 1. Taints & Node Affinity
- 전용 노드 선정 후 Taints 및 Label 적용 후 애플리케이션 배포 시 Toleration, Node Affinity 적용
- AKS Nodepool의 경우 ARM API(azcli) 로 업데이트 해야 영구적 보존 가능(바닐라로 업데이트 했을 경우, AKS 버전 업그레이드 같은 노드 교체 상황에서 기존 Taints, Label 제거됨)
```bash
# Vanila Kubernetes
k taints nodes NODE dedicated=monitoring:NoSchedule
k label nodes NODE mgmt=monitoring

# AKS
az aks nodepool update \
    --resource-group RG_NAME \
    --cluster-name CLUSTER_NAME \
    --name NODEPOOL_NAME \
    --node-taints "dedicated=monitoring:NoSchedule"

az aks nodepool update \
    --resource-group RG_NAME \
    --cluster-name CLUSTER_NAME \
    --name NODEPOOL_NAME \
    --labels mgmt=monitoring
```
### 2. LimitRange & ResourceQuota
- Application 배포시 Helm Value로 리소스 제한/요청량을 편집할 수 없는 사이드카 컨테이너들을 LimitRange를 사용하여 자동으로 리소스 제한/요청량을 적용
- 대상 네임스페이스에 자원 제한/요청량을 제한
```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: keda-compute-resources
  namespace: keda
spec:
  limits:
  - default:
      cpu: "200m"
      memory: "200Mi"
    defaultRequest:
      cpu: "100m"
      memory: "100Mi"
    type: Container
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: keda-compute-resources
  namespace: keda
spec:
  hard:
    requests.cpu: "1"
    requests.memory: "500Mi"
    limits.cpu: "2"
    limits.memory: "2Gi"
```

## Deploy Kube-Prometheus-Stack using Helm Chart
### 1. Namespace & Storage Class 생성
[promstack-storageclass-retain.yaml](./promstack/promstack-storageclass-retain.yaml)
### 2. Helm Values 편집
[promstack-helm-user-values.yaml](./promstack/promstack-helm-user-values.yaml)
### 3. Prometheus Stack 배포
```bash
helm install RELEASE prometheus-community/kube-prometheus-stack -f VALUEFILE -n NAMESPACE --version VERSION
```

## Deploy Keda using Helm Chart
### 1. Namespace 생성
```bash
k create ns keda
```
### 2. Helm Values 편집
[keda-helm-user-values.yaml](./keda/keda-helm-user-values.yaml)
### 3. Keda 배포
```bash
helm install keda kedacore/keda -n keda -f VALUEFILE
```

>Managed Prometheus 사용시 KEDA 메트릭 수집 방법
1. Helm Values에서 프로메테우스 메트릭 노출 활성화
    ```yaml
    prometheus:
    operator:
        enabled: true
    metricServer:
        enabled: true
    webhooks:
        enabled: true
    ```
2.  ServiceMonitor 배포 하여 Metrics 서비스 디스커버리 구성
*Managed Prometheus 사용시 ServiceMonitor의 apiVersion은 `azmonitoring.coreos.com/v1`

## Managed Prometheus and Managed Grafana
- Prometheus Agent 방식으로 Azure Monitor Workspace에 프로메테우스 메트릭을 Remote Write 함
- 즉, 한곳에서 멀티 클러스터의 데이터를 조회할 수 있음