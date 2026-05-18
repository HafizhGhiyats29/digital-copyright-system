import mimetypes
import sys
from pathlib import Path

import httpx
from pymilvus import Collection, connections, utility


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from config.settings import settings


MILVUS_HOST = settings["milvus_host"]
MILVUS_PORT = settings["milvus_port"]
COLLECTION_NAME = settings["milvus_collection_name"]
FEATURE_SERVICE_URL = settings["feature_service_url"]
INTERNAL_IMAGES_DIR = (ROOT_DIR / settings["internal_images_dir"]).resolve()
METADATA_ID_FIELD = settings["metadata_id_field"]
EMBEDDING_VERSION_FIELD = settings["embedding_version_field"]
EMBEDDING_VERSION = "clip-cnn-v1"


def connect_milvus():
    connections.connect(
        alias="default",
        host=MILVUS_HOST,
        port=MILVUS_PORT,
    )


def get_image_files():
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    return [
        file_path
        for file_path in INTERNAL_IMAGES_DIR.iterdir()
        if file_path.suffix.lower() in allowed_extensions
    ]


def extract_feature(image_path):
    image_bytes = image_path.read_bytes()
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"

    files = {
        "file": (image_path.name, image_bytes, mime_type),
    }

    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            FEATURE_SERVICE_URL,
            files=files,
        )
        response.raise_for_status()
        return response.json()


def insert_images_to_milvus():
    connect_milvus()

    if not utility.has_collection(COLLECTION_NAME):
        raise RuntimeError(f"Collection '{COLLECTION_NAME}' belum ada. Jalankan create_milvus_collection.py dulu.")

    collection = Collection(COLLECTION_NAME)
    image_files = get_image_files()

    if not image_files:
        print(f"Tidak ada gambar di folder: {INTERNAL_IMAGES_DIR}")
        return

    metadata_ids = []
    embedding_versions = []
    clip_embeddings = []
    cnn_embeddings = []

    for image_path in image_files:
        print(f"Processing: {image_path.name}")

        feature = extract_feature(image_path)
        clip_embedding = feature.get("clip_embedding")
        cnn_embedding = feature.get("cnn_embedding")

        if not clip_embedding or not cnn_embedding:
            print(f"Skip {image_path.name}: embedding tidak lengkap")
            continue

        if len(clip_embedding) != 512:
            print(f"Skip {image_path.name}: dimensi CLIP salah = {len(clip_embedding)}")
            continue

        if len(cnn_embedding) != 2048:
            print(f"Skip {image_path.name}: dimensi CNN salah = {len(cnn_embedding)}")
            continue

        metadata_ids.append(image_path.stem)
        embedding_versions.append(EMBEDDING_VERSION)
        clip_embeddings.append(clip_embedding)
        cnn_embeddings.append(cnn_embedding)

    if not metadata_ids:
        print("Tidak ada gambar valid untuk dimasukkan ke Milvus")
        return

    insert_data = [
        metadata_ids,
        embedding_versions,
        clip_embeddings,
        cnn_embeddings,
    ]

    collection.insert(insert_data)
    collection.flush()
    collection.load()

    print(f"Berhasil insert {len(metadata_ids)} embedding ke Milvus")
    print(f"Field metadata: {METADATA_ID_FIELD}, {EMBEDDING_VERSION_FIELD}")
    print(f"Total entities sekarang: {collection.num_entities}")


if __name__ == "__main__":
    insert_images_to_milvus()
