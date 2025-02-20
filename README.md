# IoTHub Sample Workload
# Create Offset Container
```
On the Storage account page in the Azure portal, in the Blob service section, ensure that the following settings are disabled.

Hierarchical namespace
Blob soft delete
Versioning
```
# Local ENV
```bash
# eventhub_pub_sub.py 
export BLOB_STORAGE_CONNECTION_STRING=""
export BLOB_CONTAINER_NAME=""
export EVENT_HUB_CONNECTION_STR=""
export EVENT_HUB_NAME=""
export CONSUMER_GROUP=""
export PUBLISH_EVENT_HUB_NAME=""

# eventhub_receiver.py
export BLOB_STORAGE_CONNECTION_STRING=""
export BLOB_CONTAINER_NAME=""
export EVENT_HUB_CONNECTION_STR=""
export EVENT_HUB_NAME=""
export CONSUMER_GROUP=""

# eventhub_producer.py
export EVENT_HUB_CONNECTION_STR=""
export PUBLISH_EVENT_HUB_NAME=""

# provision dps
export PROVISIONING_HOST=""
export PROVISIONING_IDSCOPE=""
export PROVISIONING_REGISTRATION_ID=""
export PROVISIONING_SYMMETRIC_KEY=""

# send message
export IOTHUB_DEVICE_CONNECTION_STRING=""

# eventhub and cosmosdb
export BLOB_STORAGE_CONNECTION_STRING=""
export BLOB_CONTAINER_NAME=""
export EVENT_HUB_CONNECTION_STR=""
export EVENT_HUB_NAME=""
export CONSUMER_GROUP=""
export COSMOS_DB_CONNECTION_STRING=""
export COSMOS_DB_DATABASE_NAME=""
export COSMOS_DB_COLLECTION_NAME=""
```
# K8s Secret
```bash
# Eventhub Secret
 k create secret generic azure-secret \
    --from-literal BLOB_STORAGE_CONNECTION_STRING="CONNSTR" \
    --from-literal BLOB_CONTAINER_NAME="CONTAINER" \
    --from-literal EVENT_HUB_CONNECTION_STR="CONNSTR" \
    --from-literal EVENT_HUB_NAME="EVENTHUB" \
    --from-literal CONSUMER_GROUP="CONSUMERGROUP" \
    --from-literal PUBLISH_EVENT_HUB_NAME="EVENTHUB"

# Eventhub - Cosmos Secret
 k create secret generic azure-secret-cosmos \
    --from-literal BLOB_STORAGE_CONNECTION_STRING="CONNSTR" \
    --from-literal BLOB_CONTAINER_NAME="CONTAINER" \
    --from-literal EVENT_HUB_CONNECTION_STR="CONNSTR" \
    --from-literal EVENT_HUB_NAME="EVENTHUB" \
    --from-literal CONSUMER_GROUP="CONSUMERGROUP" \
    --from-literal COSMOS_DB_CONNECTION_STRING="COMSMOSCONSTR" \
    --from-literal COSMOS_DB_DATABASE_NAME="COMSMOSDB" \
    --from-literal COSMOS_DB_COLLECTION_NAME="COMSMOSCOLLECTION"
```
## Eventhub Lag Monitoring
- Eventhub Lag Value = Latest Offset - Current OFfset
- Azure Monitor 집계방식은 AVG 사용해야함 (Count는 메트릭 측정값이 몇개나 수집되었는지만 확인 하므로 측정값의 합인 Sum을 Count로 나눈 AVG 만 사용할 수 있음)

# Ref
```bash
# Storage Account Connection String Scheme
DefaultEndpointsProtocol=https;AccountName=STORAGE;AccountKey=KEY
```