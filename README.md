# IoTHub Sample Workload

# Local ENV
```bash
# eventhub
export BLOB_STORAGE_CONNECTION_STRING=""
export BLOB_CONTAINER_NAME=""
export EVENT_HUB_CONNECTION_STR=""
export EVENT_HUB_NAME=""
export CONSUMER_GROUP=""

# provision dps
export PROVISIONING_HOST=""
export PROVISIONING_IDSCOPE=""
export PROVISIONING_REGISTRATION_ID=""
export PROVISIONING_SYMMETRIC_KEY=""

# send message
export IOTHUB_DEVICE_CONNECTION_STRING=""
```
# K8s Secret
```bash
# Eventhub Secret
 k create secret generic azure-secret \
    --from-literal BLOB_CONTAINER_NAME="CONTAINER" \
    --from-literal BLOB_STORAGE_CONNECTION_STRING="CONNSTR" \
    --from-literal EVENT_HUB_CONNECTION_STR="CONNSTR" \
    --from-literal EVENT_HUB_NAME="EVENTHUB" \
    --from-literal CONSUMER_GROUP="CONSUMERGROUP" \
    --from-literal PUBLISH_EVENT_HUB_NAME="EVENTHUB"
```

# Ref
```bash
# Storage Account Connection String Scheme
DefaultEndpointsProtocol=https;AccountName=STORAGE;AccountKey=KEY
```