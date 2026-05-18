import sys
from pathlib import Path

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from config.settings import settings


COLLECTION_NAME = settings["milvus_collection_name"]
MILVUS_HOST = settings["milvus_host"]
MILVUS_PORT = settings["milvus_port"]
METADATA_ID_FIELD = settings["metadata_id_field"]
EMBEDDING_VERSION_FIELD = settings["embedding_version_field"]
CLIP_FIELD = settings["clip_vector_field"]
CNN_FIELD = settings["cnn_vector_field"]
METRIC_TYPE = settings["milvus_search_metric"]


connections.connect(
    alias="default",
    host=MILVUS_HOST,
    port=MILVUS_PORT,
)


if utility.has_collection(COLLECTION_NAME):
    collection = Collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' sudah ada")
    print(collection.describe())
    raise SystemExit(0)


id_field = FieldSchema(
    name="id",
    dtype=DataType.INT64,
    is_primary=True,
    auto_id=True,
)

metadata_id_field = FieldSchema(
    name=METADATA_ID_FIELD,
    dtype=DataType.VARCHAR,
    max_length=128,
)

embedding_version_field = FieldSchema(
    name=EMBEDDING_VERSION_FIELD,
    dtype=DataType.VARCHAR,
    max_length=64,
)

clip_embedding_field = FieldSchema(
    name=CLIP_FIELD,
    dtype=DataType.FLOAT_VECTOR,
    dim=512,
)

cnn_embedding_field = FieldSchema(
    name=CNN_FIELD,
    dtype=DataType.FLOAT_VECTOR,
    dim=2048,
)

schema = CollectionSchema(
    fields=[
        id_field,
        metadata_id_field,
        embedding_version_field,
        clip_embedding_field,
        cnn_embedding_field,
    ],
    description="Copyright work embeddings linked to copyright-metadata-service records",
)

collection = Collection(
    name=COLLECTION_NAME,
    schema=schema,
)

index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": METRIC_TYPE,
    "params": {"nlist": 128},
}

collection.create_index(
    field_name=CLIP_FIELD,
    index_params=index_params,
)

collection.create_index(
    field_name=CNN_FIELD,
    index_params=index_params,
)

collection.load()

print(f"Collection '{COLLECTION_NAME}' berhasil dibuat")
print("Collections:", utility.list_collections())
print(collection.describe())
