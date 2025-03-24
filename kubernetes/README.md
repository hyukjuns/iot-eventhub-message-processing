# 오픈소스 Promstack, KEDA 배포 작업절차
1. Addon 전용 User Nodepool 추가
2. User Nodepool에 Taints & Label 적용
3. monitoring 네임스페이스 생성
4. LimitRange & Resource 적용 (Promestack + KEDA)
5. Prometheus Stack 배포
5-1. Storage Class 생성
5-2. Helm Value 파일과 함께 Prometheus Stack 배포
6. KEDA 배포
7. KEDA 이벤트허브 스케일러 배포

# 매니지드 프로메테우스 및 그라파나, KEDA 배포 작업 절차
1. Managed Prometheus, Managed Grafana 배포 (통합 Monitor Workspace 및 Managed Grafana)
2. KEDA 네임스페이스 생성
3. KEDA 배포 (Helm Charts)
4. KEDA ServiceMonitor 배포