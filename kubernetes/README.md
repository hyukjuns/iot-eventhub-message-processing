# 작업 절차 정리
1. Addon 전용 User Nodepool 추가
2. User Nodepool에 Taints & Label 적용
3. monitoring 네임스페이스 생성
4. LimitRange & Resource 적용 (Promestack + KEDA)
5. Prometheus Stack 배포
5-1. Storage Class 생성
5-2. Helm Value 파일과 함께 Prometheus Stack 배포
6. KEDA 배포
7. KEDA 이벤트허브 스케일러 배포