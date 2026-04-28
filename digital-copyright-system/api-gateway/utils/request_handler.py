from collections.abc import Mapping  # Import tipe mapping untuk headers


HOP_BY_HOP_HEADERS = {  # Daftar header yang tidak boleh diteruskan oleh proxy
    # These headers belong to one network hop and should not be forwarded.
    "connection",  # Header koneksi antar hop
    "keep-alive",  # Header keep-alive antar hop
    "proxy-authenticate",  # Header autentikasi proxy antar hop
    "proxy-authorization",  # Header otorisasi proxy antar hop
    "te",  # Header transfer encoding antar hop
    "trailer",  # Header trailer antar hop
    "transfer-encoding",  # Header encoding transfer antar hop
    "upgrade",  # Header upgrade protocol antar hop
    "host",  # Host akan dibuat ulang oleh httpx sesuai target URL
    "content-length",  # Content-Length dihitung ulang oleh HTTP client
}  # Menutup set header yang difilter


def filter_proxy_headers(headers: Mapping[str, str]) -> dict[str, str]:  # Membersihkan header sebelum proxy
    # Forward only end-to-end headers to avoid protocol-level proxy issues.
    return {  # Membuat dictionary header baru
        key: value  # Menyimpan header yang aman diteruskan
        for key, value in headers.items()  # Loop semua header dari request/response
        if key.lower() not in HOP_BY_HOP_HEADERS  # Skip header hop-by-hop
    }  # Return header yang sudah difilter
