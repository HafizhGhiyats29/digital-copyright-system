import asyncio
from typing import Optional

import cloudinary
import cloudinary.uploader

from config.settings import config


cloudinary_config = config.get("cloudinary", {})

cloudinary.config(
    cloud_name=cloudinary_config.get("cloud_name"),
    api_key=cloudinary_config.get("api_key"),
    api_secret=cloudinary_config.get("api_secret"),
    secure=True,
)


def _upload_image_sync(file_bytes: bytes, public_id: Optional[str] = None) -> dict:
    options = {
        "folder": cloudinary_config.get("folder", "copyright-registrations"),
        "resource_type": "image",
        "overwrite": False,
    }

    if public_id:
        options["public_id"] = public_id

    result = cloudinary.uploader.upload(file_bytes, **options)

    return {
        "image_url": result.get("secure_url"),
        "cloudinary_public_id": result.get("public_id"),
    }


def _delete_image_sync(public_id: str) -> None:
    return cloudinary.uploader.destroy(public_id, resource_type="image")


async def upload_image(file_bytes: bytes, public_id: Optional[str] = None) -> dict:
    return await asyncio.to_thread(_upload_image_sync, file_bytes, public_id)


async def delete_image(public_id: str) -> dict:
    return await asyncio.to_thread(_delete_image_sync, public_id)
