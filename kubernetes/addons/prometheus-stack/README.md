# Kube Prometheus Stack
Prometheus Operator 기반 kube-prometheus-stack 관리

# Todo
1. Prometheus API Auth (ex: Grafana to Promethues API)
2. Prometheus Web UI Auth

## Environments
- AKS >= 1.30.4
- Helm Chart: [kube-prometheus-stack](https://github.com/prometheus-operator/kube-prometheus)

## Prometheus Stack Component & Custom Resource Type, Resource Requests
| Component      | CPU Request | MEM Request | CPU Limit | MEM Limit | Type |
|-----------|-------------|-----------|-----------|-----------|-----------|
| Prometheus Operator | 0.5 | 256Mi | 0.5 | 512Mi| Deployment |
| Prometheus Server | 0.5 | 512Mi | 1 | 1Gi | StatefulSet |
| Alertmanager | 0.5 | 256Mi | 1 | 512Mi | StatefulSet |
| Grafana | 0.5 | 256Mi | 1 | 512Mi | StatefulSet |
| Node-exporter | 0.1 | 128Mi | 0.2 | 256Mi |  DaemonSet | 
| Kube-State-Metric | 0.1 | 128Mi | 0.2 | 256Mi | Deployment |
| + Side Car Containers 를 위한 Limit Range | 0.1| 128Mi | 0.05 | 64Mi| -|
| Sum | 2.5 | 1.875Gi | 4.5 | 3.75Gi |  - |
*Custom Value File: [main-values.yaml](/addons/prometheus-stack/values/main-values.yaml)

## Installation and Upgrade

```bash
# Create Namespace & SC
k create ns NAMESPACE
k apply -f ./objects/sample-storageclass.yaml

# Add Helm Repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Get Default Chart Value & Make Custom Values
helm show values prometheus-community/kube-prometheus-stack > values.yaml

# Check Chart Version
helm search repo prometheus-community/kube-prometheus-stack --versions | head

# Install Helm Chart
helm install RELEASE prometheus-community/kube-prometheus-stack -f VALUEFILE -n NAMESPACE --version VERSION

# Install Helm Chart (Pulled Chart)
helm install RELEASE PATH_TO_PULLED_CHART -f VALUEFILE -n NAMESPACE --version VERSION

# Upgrade or Install Helm Chart
helm upgrade --install RELEASE prometheus-community/kube-prometheus-stack -f VALUEFILE -n NAMESPACE --version VERSION
```

## Configuration

### 프로메테오스 스택 설치시 클러스터 자원 및 노드 격리
- 자원격리: LimitRange, ResourceQuota 사용
  - LimitRange: Helm Values 로 컨트롤 하기 어려운 Side Car 컨테이너에 기본 cpu/mem 요청/제한값 자동 적용 용도
  - ResourceQuota: 모니터링 네임스페이스에서 사용 가능한 총 리소스 제한
- 노드 격리: Node Affinity 사용
  - 비지니스 워크로드와 물리적으로 격리하기 위한 용도

### Ingress Basic Auth

1. Create Auth Credential

```bash
htpasswd -c auth USERNAME
k create secret generic SECRETNAME --from-file=auth -n NAMESPACE
```

2. Annotate Ingress Object

```yaml
ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: SECRETNAME
    nginx.ingress.kubernetes.io/auth-realm: "Authentication Required"
```

### Prometheus Configuration

> Prometheus Server는 Config Reloader 컨테이너를 사이드카로 사용, Prometheus Server와 Config Reloader는 EmptyDir 볼륨을 통해 설정파일을 공유

- 부트스트랩 시 prometheus.yaml 생성 과정

  1. Helm Value로 기본 설정 내용 정의 by Helm

  2. Secret Object 로 생성 by Helm
    
      - Zipped File: prometheus.yaml.gz
  
  3. Config Reloader Container 에 Secret Volume 으로 마운트

      - Secret Volume MountPath: /etc/prometheus/config/prometheus.yaml.gz

  4. EmptyDir에 압축 해제

      - EmptyDir MountPath: /etc/prometheus/config_out/prometheus.env.yaml
  
  5. Prometheus Server Container는 EmptyDir 경로에 생성된 설정 파일 사용
  
      - EmptyDir MountPath: /etc/prometheus/config_out/prometheus.env.yaml

- prometheus.yaml 샘플

  ```yaml
  # 전역설정
  global:
    scrape_interval: 15s
    scrape_timeout: 10s
    evaluation_interval: 15s

  # 별도 Rule 파일 경로
  rule_files:
    - 'prometheus.rules.yml'
    - /etc/prometheus/rules/prometheus-prometheus-kube-prometheus-prometheus-rulefiles-0/*.yaml

  # Alertmanager 설정
  alerting:
    alert_relabel_configs:
    alertmanagers:

  # Job 단위로 서비스 디스커버리
  scrape_configs:
    # 개별 수집 항목 (job은 레이블, `job=<job_name>`)
    - job_name: 'prometheus'
        # 스크랩 주기
        scrape_interval: 5s
        # 라벨 재정의
        relabel_configs:
        - source_labels: [job]
          separator: ;
          target_label: __tmp_prometheus_job_name
          replacement: $1
          action: replace
        # 쿠버네티스 서비스 디스커버리 설정
        kubernetes_sd_configs:
        - role: endpoints
          kubeconfig_file: ""
          follow_redirects: true
          enable_http2: true
          namespaces:
            own_namespace: false
            names:
            - monitoring
        # 정적 타겟 설정 (label로 그룹화 가능)
        static_configs:
        - targets: ['localhost:8080', 'localhost:8081']
            labels:
              group: 'production'
        - targets: ['localhost:8082']
            labels:
              group: 'canary'
  ```

#### Prometheus Rules (Record Rule, Alert Rule)

- 부트스트랩 시 Prometheus Rule 파일 생성 과정

  1. Helm 으로 Default Rule 설정 정의 by helm
  2. ConfigMap 으로 Rule 파일 생성 by helm
    
      - Name: <RELEASE>-prometheus-kube-prometheus-prometheus-rulefiles-0
  
  3. prometheus server container에 Rule 파일 마운트해서 사용
    
      - mount path: /etc/prometheus/rules/<RELEASE>-prometheus-kube-prometheus-prometheus-rulefiles-0
  
- PrometheusRules (CRD)로 Rule 편집 과정

  CRD로 추가한 설정은 Prometheus Operator에 의해 Prometheus Server로 업데이트 됨

  1. PrometheusRule CRD Object로 추가 설정 생성
  2. Prometheus Operator에 의해 감지
  3. Rule File ConfigMap에 업데이트 by Prometheus Operator
    
      - Name: <RELEASE>-prometheus-kube-prometheus-prometheus-rulefiles-0
  
  4. Prometheus Server에 반영됨(Reconciled) (Rule Files들은 Volume으로 마운트 되어 있음)

- Rule File 샘플

  ```yaml
  # Record Rule
  groups:
    - name: example
      rules:
      - record: code:prometheus_http_requests_total:sum
        expr: sum by (code) (prometheus_http_requests_total)

  # Alert Rule
  groups:
  - name: example
    rules:
    - alert: HighRequestLatency
      expr: job:request_latency_seconds:mean5m{job="myjob"} > 0.5
      for: 10m
      # Alertmanager 로 경고가 전달 될 때, Label 도 함께 전달됨
      # 전달된 경고의 Label은 Alertmanager 설정 중 route.routes[].matchers 와 일치하는지 비교되며, 일치되는 route 경로의 Receiver로 알람이 처리됨
      labels:
        severity: page
      annotations:
        summary: High request latency
  ```

#### Prometheus ServiceMonitor

> ServiceMonitor <- Watch -> Prometheus Operator -> Update -> Prometheus Server

메트릭 수집 엔드포인트를 정의한 ServiceMonitor는 Prometheus Operator에 의해 식별되고, Prometheus Server의 설정파일에 업데이트 됨


- Prometheus Operator의 ServiceMonitor Selector 설정

  프로메테우스 오퍼레이터가 클러스터의 모든 ServiceMonitor를 Label과 Namespace에 관계 없이 식별할 수 있도록 설정 (즉, metadata.labels 설정 불필요 (release: "RELEASE"))

    ```yaml
    prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues = false
    prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues = false
    ```

- ServiceMonitor 및 Service 샘플
    ```yaml
    apiVersion: v1
    kind: Service
    metadata:
    name: external-workload-svc
    labels:
      app: external-workload # 서비스 모니터에서 Selector 설정에 사용됨
    spec:
      selector:
        app: external-workload
    ports:
    - name: web
      port: 8080
      targetPort: 80
    - name: metrics # 서비스 모니터에서 바라보는 엔드포인트, Endpoints 설정에 사용됨
      port: 9113
      targetPort: 9113
    ---
    apiVersion: monitoring.coreos.com/v1
    kind: ServiceMonitor
    metadata:
    name: external-workload
    labels:
      software: nginx
      release: prometheus # 프로메테우스 헬름 릴리즈 이름 (필요시)
    spec:
      selector:
        matchLabels:
          app: external-workload # Service Object의 Label
        endpoints:
        - port: metrics # Service Object의 Port Name
    ```

### Alertmanager Configurations

> Alertmanager Server는 Config Reloader 컨테이너를 사이드카로 사용, Alertmanager Server와 Config Reloader는 EmptyDir 볼륨을 통해 설정파일을 공유

- 부트스트랩 시 alertmanager.yaml 생성 과정

  1. Helm Value로 기본값 정의 by helm 

  2. Secret Object 로 생성 by helm

      - Secret: alertmanager-prometheus-kube-prometheus-alertmanager-generated
      - Zipped File: alertmanager.yaml.gz

  3. Config Reloader Container 에 마운트
    
      - Secret Volume MountPath: /etc/alertmanager/config/alertmanager.yaml.gz

  4. Config Reloader Container에 의해 압축 해제 및 EmptyDir로 설정 파일 공유
  
      - EmptyDir MountPath: /etc/alertmanager/config_out/alertmanager.env.yaml

  4. Alertmanager Container는 EmptyDir 경로로 설정 파일 사용

      - EmptyDir MountPath: /etc/alertmanager/config_out/alertmanager.env.yaml


- alertmanager.yaml 샘플

  ```yaml
  global: # map, 글로벌 설정
  route:
    receiver: # str, 디폴트 라우팅
    group_by: # list, 디폴트 그룹핑
    routes: # list, 개별 라우팅 설정
    - receiver: # str, 라우팅할 리시버 이름
      matchers: # list, 경고 레이블과 일치하는지 검사, matchers 의 모든 레이블이 경고의 레이블과 일치해야 유효
  inhibit_rules: list, # 경고 억제 규칙
  - source_matchers: # 아래 레이블이 있는 경고가 발생하면
    - severity="critical"
    target_matchers: # 아래 레이블이 있는 경고는 억제됨
    - severity=~"warning|info"
    equal: # 조건은 아래 레이블의 key: value가 같아야 함
    - namespace
    - alertname
  receivers: # list, 각 리시버 설정 (슬랙,이메일 등)
  templates: # list, 경고 템플릿 파일 위치 
  ```

### AlertmanagerConfig (CRD)

> Prometheus Operator에 의해 alertmanager container에 반영됨

- Prometheus Operator가 업데이트한 alertmanager.yaml 내용 확인

  - Secret Volume 로컬로 복사 및 압축해제

    ``` k exec alertmanager-prometheus-kube-prometheus-alertmanager-0 -- tar -cf /etc/alertmanager/config/alertmanager.yaml.gz | tar -xf -```

  - 압축 해제된 설정 파일

    ```k exec alertmanager-prometheus-kube-prometheus-alertmanager-0 -- cat /etc/alertmanager/config_out/alertmanager.env.yaml```

- Default 설정 중 continue = true 로 수정

  Default 설정 중 null receiver로 빠지는 route의 continue를 true로 설정하여 개별 라우팅 경로로 경고가 흘러갈 수 있도록 설정

  ```yaml
  # In Helm Values
  alertmanager.config.route.routes[0].receiver.ontinue: true
  ```

- Alertmanager의 Global 설정 (필요시)
    
    Global AlertmanagerConfig는 Alertmanager CRD 와 같은 네임스페이스에 존재해야하며, Alertmanager 스펙 중 alertmanagerConfiguration.name에 AlertmanagerConfig 이름을 지정해 줘야함

  ```yaml
  # In Helm Values
  alertmanagerSpec.alertmanagerConfiguration.name: global-alertmanager-config
  ```

- AlertmanagerConfig의 Namespace을 route.routes.matchers에 Key로 등록되는 것 방지 (기본값: OnNamespace)

    ```yaml
    # In Helm Values
    alertmanagerSpec.alertmanagerConfigMatcherStrategy.type: None
    ```
- AlertmanagerConfig Selector 설정: Alertmanager CRD가 속한 Namespace에 있는 모든 AlertmanagerConfig만 선택되도록 설정

  ```yaml
  # In Helm Value
  alertmanagerConfigSelector: {}
  alertmanagerConfigNamespaceSelector: {} 
  ```

### Alertmanager 설정 참고

- AlertmanagerConfig(CRD)로 설정

  - https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md

  - Helm Value 사용 보다 이점: 슬랙 토큰 같은 민감 정보를 Secret 오브젝트로 만들어서 참조하기 편함

  - 슬랙 봇 토큰 및 API 정보 담은 Secret은 AlertmanagerConfig과 같은 네임스페이스에 생성 해야함

- Alertmanager Native 문법으로 작성시 Helm Value로 사용

  - https://prometheus.io/docs/alerting/latest/configuration/

      ```yaml
      # In Helm Values
      alertmanager:
        config:
          route:
              receiver: 'slack-notification' # receiver 이름
          receivers:
          - name: 'null' # default watchdog 경고 에서 사용
          - name: 'slack-notification' # receiver 이름
          slack_configs:
            - channel: '#alert-test' # 슬랙 채널 이름
              send_resolved: true
              api_url: https://slack.com/api/chat.postMessage # 슬랙 API 엔드포인트
              http_config:
                authorization:
                  type: Bearer 
                  credentials: 'BOT_TOKEN' # 슬랫 봇 토큰
      ```
### Prometheus PersistentVolume Resizing (PV)
```yaml
# Get SC Info
kubectl get storageclass -o custom-columns=NAME:.metadata.name,ALLOWVOLUMEEXPANSION:.allowVolumeExpansion
 
# Patch spec.paused==true , Set SIZE == 8Gi or 16Gi or 32Gi
kubectl -n NAMESPACE patch prometheus/NAME --patch '{"spec": {"paused": true, "storage": {"volumeClaimTemplate": {"spec": {"resources": {"requests": {"storage":"SIZE"}}}}}}}' --type merge
 
# Set 16 GB, Set SIZE == 8Gi or 16Gi or 32Gi
for p in $(kubectl -n NAMESPACE get pvc -l operator.prometheus.io/name=NAME -o jsonpath='{range .items[*]}{.metadata.name} {end}'); do \
  kubectl -n NAMESPACE patch pvc/${p} --patch '{"spec": {"resources": {"requests": {"storage":"SIZE"}}}}'; \
done
 
# Delete sts with orphan strategy 
kubectl -n NAMESPACE delete statefulset -l operator.prometheus.io/name=NAME --cascade=orphan
 
# Patch spec.paused==false 
kubectl -n NAMESPACE patch prometheus/NAME --patch '{"spec": {"paused": false}}' --type merge
```
### Prometheus, Alertmanager, Grafana PV 복구

사용시기: Chart Uninstall 후 재설치 시 Prometheus, Alertmanager, Grafana의 데이터를 보존하고 싶을 경우
주의사항: 사용하던 PV의 ReclaimPolicy가 Delete인 경우 Retain으로 변경 필요 (edit or patch)

1. Release된 PV의 Snapshot -> Managed Disk 생성
2. 수동으로 PV 생성, Managed Disk의 이름과 URI 입력 

```yaml
PersistentVolume.spec.azureDisk.diskName
PersistentVolume.spec.azureDisk.diskURI
```

3. Prometheus, Alertmanager의 경우 Helm Values에서 새로 생성한 volumeName 입력

```yaml
# alertmanager
alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.volumeName

# prometheus
prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.volumeName
```
4. Grafana의 경우 Chart를 Pull 받은 후 Template 수정 필요
  
  Grafana Chart의 statefulset.yaml Template에서는 volumeName 항목이 세팅되어 있지 않기때문에 해당 항목 세팅 후 변수로 입력 필요

  1. Kube-Prometheus-Stack Chart > Subchart > Grafana > templates > statefulset.yaml 에서 volumeName 입력

    ```yaml
    StatefulSet.spec.volumeClaimTemplates[].spec..volumeName: {{ .Values.persistence.volumeName | quote }}
    ```
  2. 배포시 사용할 Custom Values 파일에서 새로 생성한 volumeName 입력
    
    ```yaml
    grafana.persistence.volumeName
    ```
5. Helm Install or Upgrade 수행 (다운로드 받은 Helm Chart로 Install)

#### Ingress Nginx Controller 모니터링 환경 구성 (Service Monitor)

1. kuber-prometheus-stack Side

    1. kuber-prometheus-stack Helm Value 설정 편집

        ```yaml
        prometheus:
            prometheusSpec:
                podMonitorSelectorNilUsesHelmValues: false
                serviceMonitorSelectorNilUsesHelmValues: false
        ```

    2. 프로메테우스 차트 업그레이드

        ```bash
        helm upgrade -n NAMESPACE RELEASE prometheus-community/kube-prometheus-stack -f VALUEFILE --version VERSION
        ```

2. Ingress Nginx Controller Side

    1. Ingress-Nginx Controller Helm Values 설정 편집
        ```yaml
        controller:
            metrics:
                enabled: true
                serviceMonitor:
                    enabled: true
                    additionalLabels:
                        release: RELEASE # kuber-prometheus-stack's Release Name
        ```

    2. 인그레스 컨트롤러 차트 업그레이드

        ```bash
        helm upgrade -n NAMESPACE RELEASE CHART -f VALUEFILE --version VERSION
        ```

- Nginx Ingress Controller Grafana Official Dashabord

    - NGINX Ingress controller: 9614
    - Ingress Nginx / Request Handling Performance: 20510
    - Request Handling Performance: 12680

#### Uninstall Release

    1. Uninstall Helm Release
    2. Delete crd manually
        ```bash
        kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
        kubectl delete crd alertmanagers.monitoring.coreos.com
        kubectl delete crd podmonitors.monitoring.coreos.com
        kubectl delete crd probes.monitoring.coreos.com
        kubectl delete crd prometheusagents.monitoring.coreos.com
        kubectl delete crd prometheuses.monitoring.coreos.com
        kubectl delete crd prometheusrules.monitoring.coreos.com
        kubectl delete crd scrapeconfigs.monitoring.coreos.com
        kubectl delete crd servicemonitors.monitoring.coreos.com
        kubectl delete crd thanosrulers.monitoring.coreos.com
        ```
    3. Delete Service in kube-system (for kubelet)

### Reference
- [Resizing Volumes](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/platform/storage.md#resizing-volumes)
- [how-relabeling-in-prometheus-works](https://grafana.com/blog/2022/03/21/how-relabeling-in-prometheus-works/)
- [Awesome Prometheus alerts](https://samber.github.io/awesome-prometheus-alerts/)

- [Alertmanager Matcher Type Enforce Disable](https://github.com/prometheus-operator/prometheus-operator/issues/3737)

- [creating-awesome-alertmanager-templates-for-slack](https://hodovi.cc/blog/creating-awesome-alertmanager-templates-for-slack/)

- [Prometheus Operator API](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api.md#monitoring.coreos.com/v1.AlertmanagerConfigMatcherStrategy)

- [Prometheus Operator User Guide](https://github.com/prometheus-operator/prometheus-operator/tree/main/Documentation/user-guides)

- [Prometheus Alert Runbook](https://runbooks.prometheus-operator.dev/)

- [prometheus-docs](https://prometheus.io/docs/introduction/overview/)

- [kube-prometheus-stack](https://artifacthub.io/packages/helm/prometheus-community/kube-prometheus-stack)

- [prometheus-community/helm-charts Github](https://github.com/prometheus-community/helm-charts/)

- [kube-prometheus-stack Github](https://github.com/prometheus-operator/kube-prometheus)

- [Prometheus Operator](https://prometheus-operator.dev/)

- [Grafana Helm Values](https://github.com/grafana/helm-charts/tree/main/charts/grafana)

- [Nginx Ingress Controller Dashabord](https://github.com/kubernetes/ingress-nginx/tree/main/deploy/grafana/dashboards)

- [Monitor Ingress NGINX Controller](https://github.com/kubernetes/ingress-nginx/blob/main/docs/user-guide/monitoring.md#prometheus-and-grafana-installation-using-service-monitors)