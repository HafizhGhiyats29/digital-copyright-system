import httpx

from config.settings import config


EMBEDDING_SERVICE_URL = config["embedding_service_url"]
DEFAULT_EMBEDDING_VERSION = "clip-cnn-v1"


async def insert_embedding(metadata_id: str, feature: dict, embedding_version: str = DEFAULT_EMBEDDING_VERSION) -> dict:
    payload = {
        "metadata_id": metadata_id,
        "clip_embedding": feature.get("clip_embedding"),
        "cnn_embedding": feature.get("cnn_embedding"),
        "embedding_version": embedding_version,
    }

    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            EMBEDDING_SERVICE_URL,
            json=payload,
        )
        response.raise_for_status()
        return response.json()
