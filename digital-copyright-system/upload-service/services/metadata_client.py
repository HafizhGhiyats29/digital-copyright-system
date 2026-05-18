import httpx

from config.settings import config


METADATA_SERVICE_URL = config["metadata_service_url"]


async def create_metadata(metadata: dict) -> dict:
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            METADATA_SERVICE_URL,
            json=metadata,
        )
        response.raise_for_status()
        return response.json()


async def update_embedding_reference(metadata_id: str, embedding_reference: dict) -> dict:
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.patch(
            f"{METADATA_SERVICE_URL}/{metadata_id}/embedding",
            json=embedding_reference,
        )
        response.raise_for_status()
        return response.json()
