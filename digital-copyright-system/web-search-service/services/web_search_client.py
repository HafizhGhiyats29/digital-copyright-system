import httpx  # untuk HTTP request
from config.settings import config  # ambil config
from services.cloudinary_client import upload_image, delete_image  # upload & delete image
from utils.logger import logger  # logger

SERPAPI_KEY = config["serpapi_key"]  # ambil API key


async def search_image(image_bytes):

    # 1. upload ke cloudinary
    image_url, public_id = upload_image(image_bytes)
    logger.info(f"Uploaded image to Cloudinary: {image_url}")

    try:
        # 2. call serpapi
        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": SERPAPI_KEY
        }

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.get(
                "https://serpapi.com/search",
                params=params
            )

            data = response.json()
            logger.info("SerpAPI response received")

        # 3. ambil kandidat + metadata
        visual_matches = data.get("visual_matches", [])

        matches = []

        for item in visual_matches[:5]:

            match = {
                "image_url": item.get("thumbnail"),  # gambar kandidat
                "source_url": item.get("link"),      # sumber halaman
                "title": item.get("title", "")       # judul (optional)
            }

            # hanya tambahkan jika image_url ada
            if match["image_url"]:
                matches.append(match)

        logger.info(f"Found {len(matches)} candidate images")

        return {
            "found_on_web": len(matches) > 0,
            "matches": matches
        }

    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")

        return {
            "found_on_web": False,
            "matches": []
        }

    finally:
        # 4. hapus dari cloudinary (cleanup)
        delete_image(public_id)
        logger.info("Temporary image deleted from Cloudinary")