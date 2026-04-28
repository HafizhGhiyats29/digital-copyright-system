from uuid import uuid4  # Import uuid4 untuk membuat request id unik

from starlette.middleware.base import BaseHTTPMiddleware  # Base class untuk middleware Starlette
from starlette.requests import Request  # Tipe request Starlette/FastAPI


REQUEST_ID_HEADER = "X-Request-ID"  # Nama header request id yang dipakai gateway


class RequestIdMiddleware(BaseHTTPMiddleware):  # Middleware untuk request tracing
    async def dispatch(self, request: Request, call_next):  # Method yang dijalankan untuk setiap request
        # Reuse client-provided request id, or create one for tracing.
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid4()))  # Ambil request id dari header atau buat baru
        request.state.request_id = request_id  # Simpan request id di state agar bisa dipakai handler lain

        # Return the request id so clients can match responses with logs.
        response = await call_next(request)  # Lanjutkan request ke route berikutnya
        response.headers[REQUEST_ID_HEADER] = request_id  # Tambahkan request id ke response header

        return response  # Return response final ke client
