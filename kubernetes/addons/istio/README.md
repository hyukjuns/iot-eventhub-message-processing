# Istio

## Installation Step

1. Install Istio by istioctl

- [Install istioctl](https://istio.io/latest/docs/ops/diagnostic-tools/istioctl/#install-hahahugoshortcode949s2hbhb)

  ```
  curl -sL https://istio.io/downloadIstioctl | sh -
  export PATH=$HOME/.istioctl/bin:$PATH
  ```

- [Install minimal profile](https://istio.io/latest/docs/setup/install/istioctl/#install-a-different-profile)

  `istioctl install --set profile=minimal`

2. Enable SideCar Injection (Namespace 단위)

`k label namespace default istio-injection=enabled`

3. Install Kiali dashboard (istio addon)

  `k apply -f ./kiali/kiali.yaml`


## Ref
## Install kiali operator
- manifest
- helm
```bash
helm install \
    --set cr.create=true \
    --set cr.namespace=istio-system \
    --set cr.spec.auth.strategy="anonymous" \
    --namespace kiali-operator \
    --create-namespace \
    kiali-operator \
    kiali/kiali-operator
```

## Integration with Prometheus Stack (Prometheus Operator)
for Istio
1. Configure ServiceMonitor for istiod
2. Configure PodMonitor for istio Proxy or envoy sidecar

for kiali
1. Edit Configuration Kiali (config.yaml)
    Edit: configmap or manifest file
    ```
    external_services:
      prometheus:
        url: http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090
      grafana: 
        external_url: http://prometheus-grafana.monitoring.svc.cluster.local:80
        internal_url: http://prometheus-grafana.monitoring.svc.cluster.local:80
    ```