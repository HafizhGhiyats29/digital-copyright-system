import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["METADATA_STORAGE_TYPE"] = "json"
os.environ["INTERNAL_API_KEY"] = "metadata-test-internal-key"
INTERNAL_HEADERS = {"X-Internal-API-Key": os.environ["INTERNAL_API_KEY"]}

import services.metadata_store as metadata_store
from app import app


def use_isolated_json_store(monkeypatch):
    data_path = ROOT_DIR / "tests" / f"_metadata_test_{uuid4().hex}.json"
    monkeypatch.setattr(metadata_store, "DATA_DIR", data_path.parent)
    monkeypatch.setattr(metadata_store, "DATA_PATH", data_path)
    return data_path


def test_metadata_crud_and_embedding_update(monkeypatch):
    data_path = use_isolated_json_store(monkeypatch)

    client = TestClient(app, headers=INTERNAL_HEADERS)

    payload = {
        "ki_id": "4686",
        "ki_uuid": "HCNA1506232226",
        "title": "Serwataka Toguri Sharpie",
        "description": "Contoh deskripsi karya",
        "category": "HAK CIPTA",
        "sub_category": "Karya Seni",
        "copyright_category": "Karya Seni",
        "copyright_sub_category": "Seni Ilustrasi",
        "image_url": None,
        "cloudinary_public_id": None,
        "milvus_collection": None,
        "milvus_id": None,
        "embedding_version": None,
        "embedding_status": "pending",
        "report": {
            "similarity_result": {
                "overall_score": 0.42,
            },
            "decision_result": {
                "decision": {
                    "status": "no_significant_similarity",
                    "risk_level": "very_low",
                    "requires_review": False,
                },
            },
            "registration_status": "allowed",
        },
        "report_saved_at": "2026-06-10T12:00:00Z",
    }

    create_response = client.post("/metadata", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    metadata_id = created["id"]
    assert created["title"] == payload["title"]
    assert created["embedding_status"] == "pending"
    assert created["created_at"]
    assert created["updated_at"]
    assert created["report"]["similarity_result"]["overall_score"] == 0.42
    assert created["report"]["registration_status"] == "allowed"
    assert created["report_saved_at"] == "2026-06-10T12:00:00Z"

    list_response = client.get("/metadata")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/metadata/{metadata_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["ki_uuid"] == payload["ki_uuid"]

    update_response = client.put(
        f"/metadata/{metadata_id}",
        json={
            "title": "Serwataka Toguri Sharpie Updated",
            "image_url": "https://example.com/serwataka.jpg",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Serwataka Toguri Sharpie Updated"
    assert updated["image_url"] == "https://example.com/serwataka.jpg"

    embedding_response = client.patch(
        f"/metadata/{metadata_id}/embedding",
        json={
            "milvus_collection": "copyright_embeddings",
            "milvus_id": metadata_id,
            "embedding_version": "clip-cnn-v1",
            "embedding_status": "ready",
        },
    )
    assert embedding_response.status_code == 200
    embedded = embedding_response.json()
    assert embedded["milvus_collection"] == "copyright_embeddings"
    assert embedded["milvus_id"] == metadata_id
    assert embedded["embedding_version"] == "clip-cnn-v1"
    assert embedded["embedding_status"] == "ready"

    stored_items = json.loads(data_path.read_text(encoding="utf-8"))
    assert stored_items[0]["id"] == metadata_id
    assert stored_items[0]["embedding_status"] == "ready"
    assert stored_items[0]["report"]["registration_status"] == "allowed"
    assert stored_items[0]["report_saved_at"] == "2026-06-10T12:00:00Z"

    delete_response = client.delete(f"/metadata/{metadata_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "deleted", "id": metadata_id}

    missing_response = client.get(f"/metadata/{metadata_id}")
    assert missing_response.status_code == 404

    data_path.unlink(missing_ok=True)


def test_update_without_fields_returns_400(monkeypatch):
    data_path = use_isolated_json_store(monkeypatch)

    client = TestClient(app, headers=INTERNAL_HEADERS)
    create_response = client.post(
        "/metadata",
        json={
            "title": "Minimal Metadata",
            "embedding_status": "pending",
        },
    )
    metadata_id = create_response.json()["id"]

    update_response = client.put(f"/metadata/{metadata_id}", json={})
    assert update_response.status_code == 400

    data_path.unlink(missing_ok=True)
