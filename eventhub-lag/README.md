# Deploy Step

1. Setup ENV Variables
```bash
EventHubNamespace: 
EventHubName:
CheckpointAccountName:
CheckpointContainerName:
managedIdentityName:
AcaEnvName:
```

2. Deploy
```bash
az deployment group create --resource-group <resource group name> --template-file main.bicep --parameters @param.json
```
## Ref
https://github.com/Azure-Samples/eventhub-custom-metrics-emitter