import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional
from uuid import uuid4

import yaml
from pymongo import ASCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config" / "settings.yaml"
DATA_DIR = BASE_DIR / "data"
DATA_PATH = DATA_DIR / "metadata.json"
_lock = Lock()
_mongo_client: MongoClient | None = None
_mongo_collection: Collection | None = None


def _load_settings() -> dict:
    if not CONFIG_PATH.exists():
        return {}

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


settings = _load_settings()


def _storage_type() -> str:
    return os.getenv(
        "METADATA_STORAGE_TYPE",
        settings.get("storage", {}).get("type", "json"),
    ).lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text("[]", encoding="utf-8")


def _read_all_json() -> list[dict]:
    _ensure_store()
    raw = DATA_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    return json.loads(raw)


def _write_all_json(items: list[dict]) -> None:
    _ensure_store()
    DATA_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _mongo_settings() -> dict:
    mongo = settings.get("mongodb", {})
    return {
        "uri": os.getenv("MONGODB_URI", mongo.get("uri", "mongodb://localhost:27017")),
        "database": os.getenv("MONGODB_DATABASE", mongo.get("database", "digital_copyright")),
        "collection": os.getenv("MONGODB_COLLECTION", mongo.get("collection", "copyright_metadata")),
    }


def _get_mongo_collection() -> Collection:
    global _mongo_client, _mongo_collection

    if _mongo_collection is not None:
        return _mongo_collection

    mongo = _mongo_settings()
    _mongo_client = MongoClient(
        mongo["uri"],
        serverSelectionTimeoutMS=3000,
    )
    _mongo_client.admin.command("ping")
    _mongo_collection = _mongo_client[mongo["database"]][mongo["collection"]]
    _mongo_collection.create_index([("id", ASCENDING)], unique=True)
    _mongo_collection.create_index([("ki_uuid", ASCENDING)])
    _mongo_collection.create_index([("milvus_id", ASCENDING)])
    _mongo_collection.create_index([("embedding_status", ASCENDING)])
    return _mongo_collection


def _normalize_mongo_item(item: Optional[dict]) -> Optional[dict]:
    if item is None:
        return None

    item = dict(item)
    item.pop("_id", None)
    return item


def _create_metadata_json(data: dict) -> dict:
    with _lock:
        items = _read_all_json()
        now = _now_iso()
        item = {
            "id": str(uuid4()),
            **data,
            "created_at": now,
            "updated_at": now,
        }
        items.append(item)
        _write_all_json(items)
        return item


def _get_all_metadata_json() -> list[dict]:
    with _lock:
        return _read_all_json()


def _get_metadata_by_id_json(metadata_id: str) -> Optional[dict]:
    with _lock:
        for item in _read_all_json():
            if item.get("id") == metadata_id:
                return item
    return None


def _update_metadata_json(metadata_id: str, data: dict) -> Optional[dict]:
    with _lock:
        items = _read_all_json()
        for index, item in enumerate(items):
            if item.get("id") == metadata_id:
                updated = {
                    **item,
                    **data,
                    "updated_at": _now_iso(),
                }
                items[index] = updated
                _write_all_json(items)
                return updated
    return None


def _delete_metadata_json(metadata_id: str) -> bool:
    with _lock:
        items = _read_all_json()
        remaining = [item for item in items if item.get("id") != metadata_id]
        if len(remaining) == len(items):
            return False
        _write_all_json(remaining)
        return True


def _create_metadata_mongo(data: dict) -> dict:
    collection = _get_mongo_collection()
    now = _now_iso()
    item = {
        "id": str(uuid4()),
        **data,
        "created_at": now,
        "updated_at": now,
    }
    collection.insert_one(item)
    return item


def _get_all_metadata_mongo() -> list[dict]:
    collection = _get_mongo_collection()
    return [
        _normalize_mongo_item(item)
        for item in collection.find({}, {"_id": 0}).sort("created_at", ASCENDING)
    ]


def _get_metadata_by_id_mongo(metadata_id: str) -> Optional[dict]:
    collection = _get_mongo_collection()
    return _normalize_mongo_item(collection.find_one({"id": metadata_id}, {"_id": 0}))


def _update_metadata_mongo(metadata_id: str, data: dict) -> Optional[dict]:
    collection = _get_mongo_collection()
    updated = collection.find_one_and_update(
        {"id": metadata_id},
        {
            "$set": {
                **data,
                "updated_at": _now_iso(),
            },
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return _normalize_mongo_item(updated)


def _delete_metadata_mongo(metadata_id: str) -> bool:
    collection = _get_mongo_collection()
    result = collection.delete_one({"id": metadata_id})
    return result.deleted_count > 0


def create_metadata(data: dict) -> dict:
    if _storage_type() == "mongodb":
        return _create_metadata_mongo(data)
    return _create_metadata_json(data)


def get_all_metadata() -> list[dict]:
    if _storage_type() == "mongodb":
        return _get_all_metadata_mongo()
    return _get_all_metadata_json()


def get_metadata_by_id(metadata_id: str) -> Optional[dict]:
    if _storage_type() == "mongodb":
        return _get_metadata_by_id_mongo(metadata_id)
    return _get_metadata_by_id_json(metadata_id)


def update_metadata(metadata_id: str, data: dict) -> Optional[dict]:
    if _storage_type() == "mongodb":
        return _update_metadata_mongo(metadata_id, data)
    return _update_metadata_json(metadata_id, data)


def delete_metadata(metadata_id: str) -> bool:
    if _storage_type() == "mongodb":
        return _delete_metadata_mongo(metadata_id)
    return _delete_metadata_json(metadata_id)


def migrate_json_to_mongodb() -> dict:
    collection = _get_mongo_collection()
    items = _read_all_json()
    inserted = 0
    skipped = 0

    for item in items:
        if not item.get("id"):
            skipped += 1
            continue

        result = collection.update_one(
            {"id": item["id"]},
            {"$setOnInsert": item},
            upsert=True,
        )

        if result.upserted_id is not None:
            inserted += 1
        else:
            skipped += 1

    return {
        "source": str(DATA_PATH),
        "target": _mongo_settings(),
        "total": len(items),
        "inserted": inserted,
        "skipped": skipped,
    }


def check_storage_health() -> dict:
    storage = _storage_type()

    if storage != "mongodb":
        _ensure_store()
        return {
            "storage": "json",
            "path": str(DATA_PATH),
            "status": "ok",
        }

    try:
        collection = _get_mongo_collection()
        count = collection.count_documents({})
        return {
            "storage": "mongodb",
            "database": _mongo_settings()["database"],
            "collection": _mongo_settings()["collection"],
            "count": count,
            "status": "ok",
        }
    except PyMongoError as exc:
        return {
            "storage": "mongodb",
            "status": "error",
            "error": str(exc),
        }
