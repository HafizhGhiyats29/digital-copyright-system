import httpx

from config.settings import settings
from utils.logger import logger


METADATA_SERVICE_URL = settings.get("metadata_service_url", "http://localhost:8006/metadata")


async def get_metadata_by_id(metadata_id: str) -> dict | None:
    timeout = httpx.Timeout(10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{METADATA_SERVICE_URL}/{metadata_id}")

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as exc:
        logger.warning(f"Gagal mengambil metadata {metadata_id}: {exc}")
        return None


async def enrich_internal_results(internal_results: list[dict]) -> list[dict]:
    enriched_results = []

    for result in internal_results:
        metadata_id = result.get("metadata_id")

        if not metadata_id:
            enriched_results.append(result)
            continue

        metadata = await get_metadata_by_id(metadata_id)

        if metadata is None:
            continue

        if metadata.get("embedding_status") != "ready":
            continue

        enriched_results.append({
            **result,
            "metadata": {
                "id": metadata.get("id"),
                "ki_id": metadata.get("ki_id"),
                "ki_uuid": metadata.get("ki_uuid"),
                "title": metadata.get("title"),
                "description": metadata.get("description"),
                "category": metadata.get("category"),
                "sub_category": metadata.get("sub_category"),
                "copyright_category": metadata.get("copyright_category"),
                "copyright_sub_category": metadata.get("copyright_sub_category"),
                "image_url": metadata.get("image_url"),
                "cloudinary_public_id": metadata.get("cloudinary_public_id"),
                "embedding_status": metadata.get("embedding_status"),
            },
        })

    return enriched_results