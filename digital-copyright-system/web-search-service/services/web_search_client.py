import httpx  # Library untuk HTTP request async
import asyncio  # Library untuk menjalankan task async secara paralel
from config.settings import config  # Import konfigurasi aplikasi
from services.cloudinary_client import upload_image, delete_image  # Import fungsi upload dan delete Cloudinary
from utils.logger import logger  # Import logger untuk logging
from services.image_downloader import download_image  # Import fungsi download gambar kandidat
from services.feature_client import get_embedding  # Import client untuk feature extraction service

SERPAPI_KEY = config["serpapi_key"]  # Mengambil API key SerpAPI dari config


async def process_candidate(item):  # Fungsi untuk memproses satu kandidat gambar dari SerpAPI
    original_image_url = item.get("image")  # URL gambar resolusi asli jika disediakan SerpAPI
    thumbnail_url = item.get("thumbnail")  # URL thumbnail sebagai fallback
    source_url = item.get("link")  # Mengambil URL sumber kandidat
    title = item.get("title", "")  # Mengambil judul kandidat

    candidate_urls = list(dict.fromkeys(
        url for url in (original_image_url, thumbnail_url) if url
    ))

    if not candidate_urls:  # Mengecek apakah kandidat tidak punya URL gambar
        return None  # Skip kandidat jika tidak punya gambar

    for image_url_candidate in candidate_urls:
        try:  # Coba gambar asli dahulu, lalu thumbnail jika gagal
            image_bytes = await download_image(image_url_candidate)
            embedding_result = await get_embedding(image_bytes)

            clip_embedding = embedding_result.get("clip_embedding")
            cnn_embedding = embedding_result.get("cnn_embedding")

            if not clip_embedding or not cnn_embedding:
                raise ValueError("embedding tidak lengkap")

            return {
                "image_url": image_url_candidate,
                "source_url": source_url,
                "title": title,
                "clip_embedding": clip_embedding,
                "cnn_embedding": cnn_embedding,
            }
        except Exception as error:
            logger.warning(
                f"Gagal memproses kandidat {image_url_candidate}: {error}"
            )

    return None  # Semua URL kandidat gagal diproses


async def search_image(image_bytes):  # Fungsi utama web search gambar
    image_url, public_id = upload_image(image_bytes)  # Upload gambar input ke Cloudinary
    logger.info(f"Uploaded image to Cloudinary: {image_url}")  # Log URL Cloudinary

    try:  # Memulai blok utama web search
        params = {  # Parameter untuk request SerpAPI Google Lens
            "engine": "google_lens",  # Engine yang digunakan adalah Google Lens
            "url": image_url,  # URL gambar dari Cloudinary
            "api_key": SERPAPI_KEY  # API key SerpAPI
        }  # Menutup dictionary params

        timeout = httpx.Timeout(60.0)  # Timeout request ke SerpAPI

        async with httpx.AsyncClient(timeout=timeout) as client:  # Membuat HTTP client async
            response = await client.get(  # Mengirim request GET ke SerpAPI
                "https://serpapi.com/search",  # Endpoint SerpAPI
                params=params  # Parameter request
            )  # Menutup request GET

            response.raise_for_status()  # Lempar error jika status bukan 2xx
            data = response.json()  # Mengubah response menjadi JSON
            logger.info("SerpAPI response received")  # Log response diterima

        visual_matches = data.get("visual_matches", [])  # Mengambil daftar visual matches dari SerpAPI

        candidates = visual_matches[:3]  # Membatasi kandidat agar proses tidak terlalu lama

        tasks = [process_candidate(item) for item in candidates]  # Membuat task async untuk setiap kandidat

        results = await asyncio.gather(*tasks)  # Menjalankan semua kandidat secara paralel

        matches = [result for result in results if result is not None]  # Filter kandidat yang berhasil diproses

        logger.info(f"Processed {len(matches)} candidate images")  # Log jumlah kandidat berhasil

        return {  # Mengembalikan hasil akhir web search
            "found_on_web": len(matches) > 0,  # True jika ada kandidat berhasil
            "matches": matches  # List kandidat beserta CLIP + CNN embedding
        }  # Menutup dictionary response

    except Exception as e:  # Menangkap error umum web search
        logger.error(f"Error in web search: {str(e)}")  # Log error

        return {  # Mengembalikan response aman saat gagal
            "found_on_web": False,  # Tidak ditemukan karena proses gagal
            "matches": []  # List kosong
        }  # Menutup dictionary response

    finally:  # Blok cleanup selalu jalan
        delete_image(public_id)  # Menghapus gambar temporary dari Cloudinary
        logger.info("Temporary image deleted from Cloudinary")  # Log cleanup
