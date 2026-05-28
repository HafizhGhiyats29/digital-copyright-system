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
