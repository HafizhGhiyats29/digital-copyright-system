import httpx  # Import HTTP client async
from config.settings import WEB_SEARCH_SERVICE_URL  # Import URL web-search-service


async def send_to_web_search(file_bytes):  # Fungsi kirim file ke web-search-service
    timeout = httpx.Timeout(60.0)  # Timeout aman untuk proses web search

    try:  # Error handling request
        async with httpx.AsyncClient(timeout=timeout) as client:  # Membuat HTTP client dengan timeout
            files = {  # Membuat file multipart
                "image": ("image.jpg", file_bytes, "image/jpeg")  # Field harus "image" sesuai search_router.py
            }  # Menutup dictionary files

            response = await client.post(  # Mengirim request POST ke web-search-service
                WEB_SEARCH_SERVICE_URL,  # URL endpoint /search
                files=files  # File gambar yang dikirim
            )  # Menutup request

            response.raise_for_status()  # Lempar error jika response bukan 2xx

            return response.json()  # Return hasil web search

    except httpx.ConnectError:  # Jika service tidak aktif
        return {"found_on_web": False, "matches": [], "error": "Web Search Service tidak tersedia"}  # Response aman

    except httpx.ReadTimeout:  # Jika service terlalu lama
        return {"found_on_web": False, "matches": [], "error": "Web Search timeout"}  # Response timeout

    except httpx.HTTPStatusError as e:  # Jika status HTTP error
        return {"found_on_web": False, "matches": [], "error": f"Web Search HTTP error: {str(e)}"}  # Response error HTTP