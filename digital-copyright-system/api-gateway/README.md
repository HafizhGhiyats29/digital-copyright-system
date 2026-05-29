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

## Penjelasan Kode Per Fungsi

### `app.py`

#### `lifespan(app: FastAPI)`

Lifecycle aplikasi yang berjalan saat API Gateway start dan shutdown.

Logika:
- saat start, membuat `httpx.AsyncClient`;
- client disimpan ke `app.state.http_client`;
- saat shutdown, client ditutup.

Alasannya:
- request proxy antar-service memakai koneksi HTTP;
- membuat satu shared client lebih efisien daripada membuat client baru di setiap request;
- koneksi ditutup dengan benar saat aplikasi berhenti.

#### `create_app() -> FastAPI`

Factory untuk membuat instance FastAPI.

Logika:
- membuat object `FastAPI`;
- memasang middleware CORS;
- memasang middleware request id;
- mendaftarkan router health dan proxy.

Alasannya:
- struktur aplikasi lebih rapi;
- mudah diuji karena pembuatan app dipusatkan di satu fungsi.

### `config/settings.py`

#### `_load_env_file(path: Path)`

Membaca file `.env` lalu memasukkan key/value ke environment variable.

Alasannya:
- service tetap bisa jalan lokal tanpa harus set environment manual;
- nilai dari environment yang sudah ada tidak ditimpa.

#### `_load_yaml(path: Path) -> dict`

Membaca konfigurasi YAML.

Alasannya:
- default konfigurasi lebih mudah dibaca dan dirawat di `settings.yaml`.

#### `_get_env(name: str, default: Any) -> Any`

Mengambil environment variable dengan fallback default.

Alasannya:
- konfigurasi bisa dioverride dari `.env` atau Docker.

#### `_get_list_env(name: str, default: list[str]) -> list[str]`

Mengambil environment variable berbentuk list yang dipisah koma.

Dipakai untuk:
- daftar allowed origins CORS.

Alasannya:
- satu variable `.env` bisa menyimpan banyak origin frontend.

#### `ServiceConfig`

Dataclass untuk menyimpan URL service internal.

Alasannya:
- URL service tidak tersebar sebagai string mentah di banyak file.

#### `Settings`

Dataclass konfigurasi gateway.

Berisi:
- konfigurasi service internal,
- CORS,
- internal API key.

#### `load_settings() -> Settings`

Menggabungkan konfigurasi dari YAML dan environment.

Alasannya:
- YAML menjadi default;
- `.env` atau Docker environment dapat override nilai sesuai environment.

### `middleware/request_id.py`

#### `RequestIdMiddleware.dispatch(request, call_next)`

Menambahkan `X-Request-ID` pada request dan response.

Alur:
1. Ambil request id dari header jika ada.
2. Jika tidak ada, buat UUID baru.
3. Simpan ke `request.state.request_id`.
4. Lanjutkan request ke handler berikutnya.
5. Tambahkan request id ke response.

Alasannya:
- memudahkan tracing request lintas-service.

### `router/health_routes.py`

#### `health()`

Health check dasar API Gateway.

Output:

```json
{"status": "ok"}
```

#### `api_health()`

Health check versi API.

Biasanya dipakai jika ingin membedakan endpoint root health dan endpoint API health.

#### `services_health(request: Request)`

Mengecek health service internal.

Logika:
- memanggil endpoint health dari service-service internal;
- mengembalikan status gabungan.

Alasannya:
- dari satu endpoint gateway, developer bisa tahu service mana yang hidup atau mati.

### `utils/request_handler.py`

#### `filter_proxy_headers(headers)`

Membersihkan header sebelum diteruskan ke service internal.

Header seperti `host` dan header transfer tertentu tidak perlu ikut diteruskan.

Alasannya:
- mencegah konflik header antara client, gateway, dan service internal.

### `utils/proxy.py`

#### `build_target_url(service_name: str, path: str) -> str`

Membentuk URL tujuan service internal.

Input:
- nama service,
- path endpoint.

Output:
- URL lengkap ke upstream service.

Alasannya:
- logic pembentukan URL hanya ada di satu tempat.

#### `proxy_request(request: Request, service_name: str, path: str) -> Response`

Proxy umum untuk request JSON atau request biasa.

Alur:
1. Ambil method, query, body, dan header dari request.
2. Bangun URL target.
3. Tambahkan internal API key.
4. Kirim request ke service tujuan.
5. Kembalikan response service tujuan ke client.

Alasannya:
- API Gateway tidak perlu menulis ulang logic HTTP untuk setiap endpoint.

#### `proxy_multipart_request(...)`

Proxy khusus multipart upload.

Dipakai untuk:
- upload file gambar ke upload service.

Alasannya:
- multipart tidak bisa selalu diperlakukan sama seperti JSON body;
- file harus dibangun ulang agar bisa diteruskan dengan benar.

### `router/proxy_routes.py`

#### Schema metadata dan register

Class seperti `MetadataBase`, `MetadataCreate`, `MetadataUpdate`, `EmbeddingReferenceUpdate`, `MetadataResponse`, `RegisterMetadataRequest`, dan `ReviewCheckRequest` dipakai untuk dokumentasi OpenAPI gateway.

Alasannya:
- Swagger API Gateway menampilkan body request yang jelas;
- developer frontend tidak perlu membuka service internal hanya untuk melihat bentuk payload.

#### `upload(...)`

Endpoint gateway untuk upload gambar.

Logika:
- menerima file dan pilihan threshold dari frontend;
- meneruskan multipart request ke upload service.

#### `register_metadata(...)`

Endpoint gateway untuk registrasi metadata setelah pengecekan plagiarisme.

Logika:
- menerima `check_id` dan data metadata;
- meneruskan request ke upload service;
- upload service yang mengatur Cloudinary, MongoDB, dan Milvus.

#### `approve_check(...)` dan `reject_check(...)`

Endpoint review manual.

Fungsi:
- approve membuat `check_id` boleh dipakai untuk registrasi;
- reject membuat `check_id` tidak boleh dipakai.

#### `metadata_collection(request)`

Proxy untuk list metadata.

#### `create_metadata_item(...)`

Proxy untuk create metadata langsung.

Catatan:
- untuk workflow normal setelah plagiarisme check, gunakan `register_metadata`;
- endpoint CRUD langsung berguna untuk administrasi atau testing.

#### `read_metadata_item(...)`

Mengambil detail metadata berdasarkan ID.

#### `update_metadata_item(...)`

Update metadata parsial.

#### `update_metadata_embedding(...)`

Update referensi embedding metadata.

Biasanya dipakai setelah embedding berhasil disimpan ke Milvus.

#### `delete_metadata_item(...)`

Delete lengkap dari gateway.

Alur cleanup:
1. Ambil detail metadata.
2. Hapus gambar Cloudinary jika ada `cloudinary_public_id`.
3. Hapus vector Milvus jika ada `milvus_id` atau `metadata_id`.
4. Hapus metadata dari MongoDB.
5. Kembalikan ringkasan cleanup.

Alasannya:
- delete metadata harus membersihkan semua resource terkait.

#### `delete_metadata_vector(...)`

Menghapus vector Milvus berdasarkan metadata ID.

Alasannya:
- disediakan sebagai endpoint khusus jika perlu cleanup vector saja.
