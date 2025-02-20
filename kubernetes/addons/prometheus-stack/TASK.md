작업포인트
- PV 회수정책 Retain 설정을 위한 StorageClass 생성
- 네임스페이스 자원 격리를 위한 LimitRange, ResourceQuota 적용, LimitRange로 Helm Values로 컨트롤 불가능한 Side Car 컨테이너에 Requests, Limit 자동 적용
- 노드 격리를 위한 Taint, Label 작업
1. Node Drain
2. Node Taint
3. Node Uncordon
4. Node Label
- Helm 배포시 Node Affinity, Toleration 적용
