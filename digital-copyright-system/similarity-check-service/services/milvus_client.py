from pymilvus import Collection, connections, utility

from config.settings import settings
from utils.logger import logger


MILVUS_HOST = settings["milvus_host"]
MILVUS_PORT = settings["milvus_port"]
COLLECTION_NAME = settings["milvus_collection_name"]
METADATA_ID_FIELD = settings["metadata_id_field"]
EMBEDDING_VERSION_FIELD = settings["embedding_version_field"]
CLIP_FIELD = settings["clip_vector_field"]
CNN_FIELD = settings["cnn_vector_field"]
METRIC_TYPE = settings["milvus_search_metric"]


def get_collection():
    connections.connect(
        alias="default",
        host=MILVUS_HOST,
        port=MILVUS_PORT,
    )

    if not utility.has_collection(COLLECTION_NAME):
        logger.warning(f"Milvus collection tidak ditemukan: {COLLECTION_NAME}")
        return None

    collection = Collection(COLLECTION_NAME)
    collection.load()
    return collection


def validate_embedding_dimensions(clip_embedding, cnn_embedding):
    if len(clip_embedding) != 512:
        raise ValueError(f"Dimensi CLIP harus 512, diterima {len(clip_embedding)}")

    if len(cnn_embedding) != 2048:
        raise ValueError(f"Dimensi CNN harus 2048, diterima {len(cnn_embedding)}")


def insert_embedding(metadata_id, clip_embedding, cnn_embedding, embedding_version="clip-cnn-v1"):
    validate_embedding_dimensions(clip_embedding, cnn_embedding)
    collection = get_collection()

    if collection is None:
        raise RuntimeError(f"Milvus collection tidak ditemukan: {COLLECTION_NAME}")

    insert_data = [
        [metadata_id],
        [embedding_version],
        [clip_embedding],
        [cnn_embedding],
    ]

    result = collection.insert(insert_data)
    collection.flush()
    collection.load()

    primary_keys = list(result.primary_keys)
    return {
        "milvus_collection": COLLECTION_NAME,
        "milvus_id": str(primary_keys[0]) if primary_keys else None,
        "metadata_id": metadata_id,
        "embedding_version": embedding_version,
    }


def search_single_vector(collection, query_embedding, vector_field, top_k):
    search_params = {
        "metric_type": METRIC_TYPE,
        "params": {"nprobe": 10},
    }

    results = collection.search(
        data=[query_embedding],
        anns_field=vector_field,
        param=search_params,
        limit=top_k,
        output_fields=[
            METADATA_ID_FIELD,
            EMBEDDING_VERSION_FIELD,
        ],
    )

    output = []

    for hit in results[0]:
        entity = hit.entity

        output.append({
            "milvus_id": str(hit.id),
            "score": float(hit.score),
            "metadata_id": entity.get(METADATA_ID_FIELD),
            "embedding_version": entity.get(EMBEDDING_VERSION_FIELD),
        })

    return output


def merge_internal_results(clip_results, cnn_results):
    merged = {}

    for item in clip_results:
        item_id = item["milvus_id"]
        merged[item_id] = {
            **item,
            "clip_score": item["score"],
            "cnn_score": 0.0,
        }

    for item in cnn_results:
        item_id = item["milvus_id"]

        if item_id not in merged:
            merged[item_id] = {
                **item,
                "clip_score": 0.0,
                "cnn_score": item["score"],
            }
        else:
            merged[item_id]["cnn_score"] = item["score"]

    return list(merged.values())


def search_internal_similarity(query_clip_embedding, query_cnn_embedding, top_k=3):
    collection = get_collection()

    if collection is None:
        return []

    clip_results = search_single_vector(
        collection=collection,
        query_embedding=query_clip_embedding,
        vector_field=CLIP_FIELD,
        top_k=top_k,
    )

    cnn_results = search_single_vector(
        collection=collection,
        query_embedding=query_cnn_embedding,
        vector_field=CNN_FIELD,
        top_k=top_k,
    )

    merged_results = merge_internal_results(clip_results, cnn_results)

    clip_weight = settings["clip_weight"]
    cnn_weight = settings["cnn_weight"]

    final_results = []

    for item in merged_results:
        final_score = (item["clip_score"] * clip_weight) + (item["cnn_score"] * cnn_weight)

        final_results.append({
            "source": "internal",
            "final_score": float(final_score),
            "clip_score": float(item["clip_score"]),
            "cnn_score": float(item["cnn_score"]),
            "milvus_id": item.get("milvus_id"),
            "metadata_id": item.get("metadata_id"),
            "embedding_version": item.get("embedding_version"),
        })

    final_results = sorted(
        final_results,
        key=lambda x: x["final_score"],
        reverse=True,
    )

    return final_results[:top_k]


def _escape_milvus_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def delete_embedding_by_metadata_id(metadata_id: str):
    collection = get_collection()

    if collection is None:
        raise RuntimeError(f"Milvus collection tidak ditemukan: {COLLECTION_NAME}")

    safe_metadata_id = _escape_milvus_string(metadata_id)
    expr = f'{METADATA_ID_FIELD} == "{safe_metadata_id}"'

    existing = collection.query(
        expr=expr,
        output_fields=[METADATA_ID_FIELD],
    )

    if not existing:
        return {
            "milvus_collection": COLLECTION_NAME,
            "metadata_id": metadata_id,
            "deleted_count": 0,
        }

    result = collection.delete(expr)
    collection.flush()
    collection.load()

    deleted_count = getattr(result, "delete_count", None)
    if deleted_count is None:
        deleted_count = len(existing)

    return {
        "milvus_collection": COLLECTION_NAME,
        "metadata_id": metadata_id,
        "deleted_count": int(deleted_count),
    }
