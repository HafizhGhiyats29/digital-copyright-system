# Upload Service - Panduan Memahami Kode

Upload service adalah orkestrator utama proses pengecekan plagiarisme dan registrasi metadata. Service ini tidak menghitung embedding sendiri, tetapi memanggil service lain sesuai kebutuhan.

## Tanggung Jawab Utama

- Menerima file gambar dari frontend.
- Memvalidasi file gambar.
- Memanggil feature extraction service untuk membuat embedding CLIP dan CNN.
- Memanggil web search service untuk mencari kandidat eksternal.
- Memanggil similarity-check service untuk menghitung kemiripan.
- Memanggil decision engine untuk menentukan status risiko.
- Menyimpan embedding sementara berdasarkan `check_id`.
- Mengizinkan registrasi metadata hanya jika hasil pengecekan aman atau sudah disetujui manual.
- Mengunggah gambar ke Cloudinary saat metadata benar-benar didaftarkan.
- Mengirim metadata ke copyright-metadata-service.
- Menyimpan embedding final ke Milvus melalui similarity-check service.

## File Penting

### `app.py`

Entry point FastAPI upload service.

Logika utamanya:
- Membuat aplikasi FastAPI.
- Mendaftarkan router upload.
- Mengaktifkan middleware CORS.

### `routers/upload_router.py`

File ini berisi alur utama upload dan registrasi.

Endpoint penting:
- upload gambar untuk cek plagiarisme,
- register metadata dari hasil cek,
- approve hasil review manual,
- reject hasil review manual.

Alur cek plagiarisme:
1. Validasi file berdasarkan content type, ukuran, dan isi gambar.
2. Kirim gambar ke feature extraction service.
3. Ambil hasil embedding CLIP dan CNN.
4. Cari kandidat eksternal melalui web search service.
5. Kirim embedding dan kandidat ke similarity-check service.
6. Kirim skor terbaik ke decision engine.
7. Simpan embedding sementara dengan `check_id`.
8. Kembalikan hasil ke frontend.

Alur register metadata:
1. Frontend mengirim `check_id` dan data metadata.
2. Service mengecek hasil keputusan sebelumnya.
3. Jika status aman atau sudah di-approve, gambar diunggah ke Cloudinary.
4. Metadata dibuat di metadata service.
5. Embedding sementara dipromosikan ke Milvus.
6. Metadata di-update dengan referensi Milvus.
7. Embedding sementara dihapus.

Alasannya:
- Embedding tidak dihitung dua kali.
- Gambar baru hanya masuk ke database internal jika sudah lolos pengecekan.
- `check_id` menjadi penghubung antara hasil cek dan proses registrasi.

### `utils/image_validator.py`

Berisi validasi keamanan file gambar.

Validasi yang dilakukan:
- file tidak kosong,
- format hanya JPEG, PNG, atau WEBP,
- ukuran file tidak melebihi batas konfigurasi,
- gambar benar-benar bisa dibaca oleh PIL,
- total pixel tidak melebihi batas aman.

Alasannya:
- Mencegah file rusak atau file non-gambar masuk ke pipeline ML.
- Mengurangi risiko memory spike dari gambar yang terlalu besar.
- Menjaga service feature extraction tetap stabil.

### `services/temporary_embedding_store.py`

Menyimpan hasil embedding sementara berdasarkan `check_id`.

Data ini dipakai saat:
- hasil cek plagiarisme aman,
- user melanjutkan ke registrasi metadata,
- embedding yang sama dipakai untuk disimpan ke Milvus.

Alasannya:
- Pipeline menjadi lebih efisien karena embedding tidak perlu dibuat ulang.
- `check_id` menjadi bukti bahwa metadata yang didaftarkan berasal dari gambar yang sudah diperiksa.

### Client Service

Folder `services/` berisi client untuk memanggil service lain:

- `feature_client.py`: memanggil feature extraction service.
- `web_search_client.py`: memanggil web search service.
- `similarity_client.py`: memanggil similarity-check service.
- `decision_client.py`: memanggil decision engine.
- `metadata_client.py`: memanggil copyright-metadata-service.
- `embedding_client.py`: menyimpan/menghapus vector di Milvus melalui similarity-check service.
- `cloudinary_client.py`: upload dan hapus gambar Cloudinary.

Alasannya:
- Router tidak perlu tahu detail URL, header, dan format request setiap service.
- Kode lebih mudah diuji dan dirawat.

## Catatan Desain

Upload service adalah pusat workflow. Service ini tidak menyimpan data permanen sendiri. Data permanen tetap berada di:

- MongoDB melalui copyright-metadata-service,
- Milvus melalui similarity-check service,
- Cloudinary untuk file gambar.

Dengan pemisahan ini, upload service fokus pada proses, bukan penyimpanan.
