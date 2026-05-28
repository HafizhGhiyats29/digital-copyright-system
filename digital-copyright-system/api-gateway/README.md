# API Gateway - Panduan Memahami Kode

Service ini menjadi pintu masuk utama untuk frontend. Frontend cukup memanggil API Gateway, lalu gateway meneruskan request ke service internal seperti upload, similarity, decision, metadata, feature extraction, dan web search.

## Tanggung Jawab Utama

- Menyediakan satu base URL publik untuk frontend.
- Meneruskan request ke service internal melalui proxy.
- Menambahkan internal API key saat berkomunikasi antar-service.
- Mengatur CORS agar frontend dapat mengakses backend.
- Menyediakan endpoint health check.
- Mengorkestrasi penghapusan metadata, vector Milvus, dan file Cloudinary pada satu endpoint delete.

## File Penting

### `app.py`

File entrypoint FastAPI.

Logika utamanya:
- Membuat instance `FastAPI`.
- Mendaftarkan middleware CORS.
- Mendaftarkan router health dan proxy.
- Membuat shared `httpx.AsyncClient` saat aplikasi hidup.

Alasannya:
- `httpx.AsyncClient` dipakai agar request antar-service lebih efisien.
- API Gateway tidak menyimpan business logic berat, hanya routing dan orkestrasi ringan.

### `config/settings.py`

Mengambil konfigurasi dari `.env` dan `settings.yaml`.

Konfigurasi yang penting:
- URL masing-masing service internal.
- API key internal.
- daftar origin frontend untuk CORS.

Alasannya:
- Nilai seperti URL service dan secret tidak dikunci di kode.
- Saat dijalankan lewat Docker, alamat service bisa berubah menjadi nama container seperti `http://upload-service:8001`.
- Saat dijalankan lokal, alamat bisa tetap `http://localhost:8001`.

### `router/health_routes.py`

Menyediakan endpoint untuk mengecek apakah API Gateway aktif.

Biasanya dipakai untuk:
- pengecekan manual,
- Docker health check,
- debugging ketika service lain tidak bisa diakses.

### `router/proxy_routes.py`

Berisi mapping endpoint publik ke service internal.

Contoh tanggung jawab:
- `/api/v1/upload` diteruskan ke upload service.
- `/api/v1/metadata` diteruskan ke metadata service.
- `/api/v1/decision` diteruskan ke decision engine.

Endpoint delete metadata memiliki logika khusus:
- hapus file dari Cloudinary,
- hapus vector dari Milvus,
- hapus metadata dari MongoDB,
- lalu mengembalikan laporan cleanup.

Alasannya:
- Delete metadata bukan hanya menghapus record database.
- Data yang terkait tersebar di tiga tempat: metadata storage, object storage, dan vector database.
- Gateway cocok menjadi orkestrator untuk operasi lintas-service seperti ini.

### `utils/proxy.py`

Berisi helper untuk meneruskan request ke service internal.

Logika penting:
- Mengambil method, path, query, body, dan header dari request asli.
- Membuat request baru ke target service.
- Menambahkan `X-Internal-API-Key`.
- Mengembalikan response service internal ke client.

Alasannya:
- Menghindari duplikasi kode proxy di setiap route.
- Menjaga internal service tetap tidak terbuka bebas tanpa API key.

### `middleware/request_id.py`

Menambahkan request id pada setiap request.

Alasannya:
- Memudahkan tracing log ketika satu request frontend melewati banyak service.
- Berguna saat debugging error lintas-service.

## Alur Request Umum

1. Frontend mengirim request ke API Gateway.
2. API Gateway membaca path endpoint.
3. Gateway memilih service tujuan.
4. Gateway meneruskan request dengan internal API key.
5. Service internal memproses request.
6. Gateway mengembalikan response ke frontend.

## Catatan Desain

API Gateway sengaja dibuat tipis. Business logic utama tetap berada di service masing-masing. Dengan pola ini, perubahan logic similarity, decision, atau metadata tidak perlu mengubah gateway terlalu banyak.
