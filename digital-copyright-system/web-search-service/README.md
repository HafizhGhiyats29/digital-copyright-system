# Web Search Service - Panduan Memahami Kode

Web search service bertugas mencari kandidat gambar dari internet. Kandidat ini kemudian dibandingkan dengan gambar yang diupload user.

## Tanggung Jawab Utama

- Mengunggah gambar query sementara ke Cloudinary jika diperlukan.
- Melakukan reverse image search atau pencarian gambar melalui API eksternal.
- Mengambil daftar kandidat gambar dari web.
- Mengunduh gambar kandidat.
- Mengirim kandidat ke feature extraction service untuk dibuat embedding.
- Mengembalikan kandidat eksternal beserta embedding dan sumber URL.

## File Penting

### `app.py`

Entry point FastAPI web search service.

Logika utamanya:
- Membuat aplikasi FastAPI.
- Mendaftarkan router search.
- Mengaktifkan konfigurasi dasar service.

### `routers/search_router.py`

Berisi endpoint pencarian web.

Alur umumnya:
1. Menerima gambar dari upload service.
2. Memanggil web search client untuk mencari kandidat.
3. Mengunduh gambar kandidat.
4. Mengekstrak fitur kandidat.
5. Mengembalikan hasil kandidat eksternal.

Alasannya:
- Upload service cukup meminta hasil pencarian.
- Detail API eksternal disembunyikan di service ini.

### `services/web_search_client.py`

Berisi komunikasi dengan provider pencarian gambar.

Tugasnya:
- memanggil API pencarian,
- membaca response provider,
- mengambil `image_url`, `source_url`, dan `title`.

Alasannya:
- Provider pencarian bisa berubah.
- Jika API eksternal diganti, perubahan cukup dilakukan di client ini.

### `services/image_downloader.py`

Mengunduh gambar kandidat dari URL eksternal.

Alasannya:
- Kandidat web perlu diubah menjadi embedding agar bisa dibandingkan dengan gambar query.
- Download dipisah agar logic network dan error handling lebih jelas.

### `services/feature_client.py`

Memanggil feature extraction service untuk kandidat eksternal.

Alasannya:
- Web search service tidak menjalankan model ML sendiri.
- Semua embedding tetap dibuat dengan pipeline yang sama seperti gambar upload.

### `services/cloudinary_client.py`

Membantu upload gambar query sementara jika provider pencarian membutuhkan URL publik.

Alasannya:
- Beberapa layanan reverse image search membutuhkan URL gambar yang bisa diakses publik.
- File lokal dari user tidak bisa langsung diakses oleh API eksternal.

### `schemas/response_schema.py`

Mendefinisikan struktur response hasil pencarian.

Alasannya:
- Upload service membutuhkan response yang konsisten.
- Kandidat eksternal harus memiliki URL gambar, sumber, judul, dan embedding jika tersedia.

## Catatan Desain

Web search dipisahkan karena bergantung pada layanan eksternal dan jaringan. Jika web search gagal, sistem masih bisa menggunakan pencarian internal dari Milvus. Pemisahan ini juga membuat service lain tetap stabil walaupun API eksternal mengalami gangguan.

## Penjelasan Kode Per Fungsi

### `app.py`

#### `health()`

Endpoint health check service.

Alasannya:
- memastikan service pencarian web aktif sebelum dipakai upload service.

### `routers/search_router.py`

#### `search(image: UploadFile = File(...))`

Endpoint utama web search.

Alur:
1. Menerima gambar dari upload service.
2. Membaca file menjadi bytes.
3. Memanggil `search_image(image_bytes)`.
4. Mengembalikan daftar kandidat eksternal.

Alasannya:
- router tetap fokus ke HTTP;
- logic pencarian eksternal dipindahkan ke service.

### `services/cloudinary_client.py`

#### `upload_image(file_bytes)`

Mengunggah gambar query ke Cloudinary.

Alasannya:
- beberapa API reverse image search membutuhkan URL publik;
- gambar lokal user tidak bisa langsung diakses oleh provider eksternal.

#### `delete_image(public_id)`

Menghapus gambar dari Cloudinary berdasarkan public ID.

Alasannya:
- gambar sementara tidak perlu disimpan selamanya.

### `services/feature_client.py`

#### `get_embedding(image_bytes)`

Meminta embedding ke feature extraction service.

Alur:
1. Kirim bytes gambar kandidat.
2. Terima embedding CLIP dan CNN.
3. Return embedding untuk similarity service.

Alasannya:
- web search service tidak membawa model ML sendiri.

### `services/image_downloader.py`

#### `download_image(url)`

Mengunduh gambar kandidat dari URL eksternal.

Alasannya:
- gambar kandidat perlu diubah menjadi embedding sebelum dibandingkan.

### `services/web_search_client.py`

#### `process_candidate(item)`

Memproses satu kandidat hasil web search.

Alur umum:
1. Ambil `image_url`, `source_url`, dan `title`.
2. Download gambar kandidat.
3. Ambil embedding kandidat.
4. Bentuk item kandidat yang siap dikirim ke similarity service.

Alasannya:
- setiap kandidat perlu diproses seragam.
- kandidat gagal download atau gagal embedding bisa ditangani tanpa mematikan seluruh proses.

#### `search_image(image_bytes)`

Fungsi utama pencarian gambar eksternal.

Alur:
1. Upload gambar query jika dibutuhkan provider.
2. Panggil API pencarian gambar.
3. Ambil daftar kandidat.
4. Proses kandidat satu per satu dengan `process_candidate`.
5. Kembalikan hasil eksternal.

Alasannya:
- web search bergantung pada provider luar;
- logic provider dibungkus agar upload service tidak perlu tahu detailnya.

### `schemas/response_schema.py`

#### `MatchItem`

Schema satu kandidat eksternal.

Field umum:
- `image_url`;
- `source_url`;
- `title`;
- embedding jika tersedia.

#### `SearchResponse`

Schema response utama web search.

Alasannya:
- hasil web search harus konsisten untuk similarity-check service.

### `utils/internal_auth.py`

Fungsi-fungsi di file ini sama polanya dengan service lain:

- `_load_env_file`: memuat `.env`;
- `get_internal_api_key`: membaca API key;
- `internal_auth_headers`: membuat header internal;
- `require_internal_api_key`: melindungi endpoint internal.
