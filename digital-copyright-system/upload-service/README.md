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

## Penjelasan Kode Per Fungsi

### `app.py`

#### `health()`

Endpoint health check upload service.

Alasannya:
- memastikan service orkestrator siap menerima request upload.

### `utils/image_validator.py`

#### `validate_image(file_bytes)`

Memvalidasi isi file gambar.

Validasi:
- file tidak kosong;
- gambar bisa dibuka oleh PIL;
- format termasuk JPEG, PNG, atau WEBP;
- total pixel tidak melebihi batas aman;
- gambar lolos `image.verify()`.

Alasannya:
- validasi content type dari browser belum cukup;
- file bisa saja berekstensi gambar tetapi isinya rusak atau bukan gambar;
- batas pixel mencegah gambar terlalu besar membebani memory.

### `routers/upload_router.py`

#### `RegisterMetadataRequest`

Schema request registrasi metadata setelah pengecekan plagiarisme.

Field penting:
- `check_id`;
- `title`;
- `description`;
- kategori karya.

Alasannya:
- metadata hanya boleh didaftarkan jika punya `check_id` dari proses pengecekan.

#### `ReviewCheckRequest`

Schema request untuk approve/reject manual.

Field:
- `reason` opsional.

Alasannya:
- reviewer bisa memberi alasan keputusan manual.

#### `DeleteCloudinaryRequest`

Schema request hapus gambar Cloudinary.

Field:
- `public_id`.

Alasannya:
- delete gambar Cloudinary membutuhkan public ID, bukan URL.

#### `build_cloudinary_public_id(title: str, identifier: Optional[str])`

Membuat nama file Cloudinary yang mudah dibaca dan tetap unik.

Logika:
- title dibuat slug;
- identifier seperti `check_id` atau metadata ID ditambahkan agar tidak tabrakan.

Alasannya:
- nama file seperti `judul-karya-uuid` lebih mudah dipahami dibanding ID acak saja;
- tetap unik walaupun title sama.

#### `build_registration_gate(decision_result)`

Mengubah hasil decision engine menjadi status registrasi.

Output utama:
- `can_register`;
- `registration_status`;
- `registration_reason`.

Logika umum:
- high similarity -> blocked;
- medium/possible -> review_required;
- low/no significant -> allowed.

Alasannya:
- decision engine hanya memberi keputusan risiko;
- upload service menerjemahkan risiko menjadi boleh/tidaknya registrasi.

#### `register_metadata(data: RegisterMetadataRequest)`

Endpoint registrasi metadata setelah gambar dicek.

Alur:
1. Ambil temporary embedding berdasarkan `check_id`.
2. Pastikan `check_id` ada.
3. Pastikan hasilnya allowed atau sudah approved.
4. Upload gambar ke Cloudinary.
5. Create metadata ke metadata service.
6. Insert embedding ke Milvus melalui similarity service.
7. Update metadata dengan referensi Milvus.
8. Hapus temporary embedding.
9. Return metadata dan status embedding.

Alasannya:
- gambar tidak boleh langsung masuk database sebelum lolos pengecekan;
- embedding yang sudah dibuat saat upload dipakai ulang;
- metadata, gambar, dan vector dibuat dalam satu workflow.

#### `approve_check(check_id, data)`

Mengubah hasil review manual menjadi approved.

Alur:
- cari temporary embedding;
- tandai sebagai approved;
- ubah status agar bisa lanjut register metadata.

Alasannya:
- kasus medium/possible tidak langsung ditolak;
- reviewer bisa memutuskan bahwa karya tetap aman.

#### `reject_check(check_id, data)`

Mengubah hasil review manual menjadi rejected.

Alur:
- cari temporary embedding;
- tandai sebagai rejected;
- registrasi tidak boleh lanjut.

Alasannya:
- reviewer bisa memblokir karya yang dinilai berisiko.

#### `delete_cloudinary_image(data)`

Menghapus gambar dari Cloudinary.

Biasanya dipakai oleh API Gateway saat cleanup delete metadata.

#### `upload_image(...)`

Endpoint utama cek plagiarisme.

Alur lengkap:
1. Validasi content type.
2. Baca bytes file.
3. Validasi ukuran dan isi gambar.
4. Kirim ke feature extraction service.
5. Kirim ke web search service.
6. Kirim embedding dan kandidat eksternal ke similarity-check service.
7. Kirim skor terbaik ke decision engine.
8. Bangun status registrasi.
9. Simpan temporary embedding dengan `check_id`.
10. Return response lengkap ke frontend.

Alasannya:
- upload service menjadi koordinator semua service;
- frontend cukup memanggil satu endpoint untuk seluruh proses pengecekan.

### `services/temporary_embedding_store.py`

#### `_now()`

Menghasilkan waktu sekarang.

Dipakai untuk:
- mencatat created time temporary embedding;
- menghitung expired data.

#### `_cleanup_expired()`

Membersihkan temporary embedding yang sudah melewati TTL.

Alasannya:
- temporary store tidak boleh menumpuk selamanya di memory.

#### `save_temporary_embedding(...)`

Menyimpan embedding sementara berdasarkan `check_id`.

Data yang disimpan:
- feature CLIP/CNN;
- hasil decision;
- status registrasi;
- bytes gambar;
- filename.

Alasannya:
- saat user lanjut register metadata, sistem tidak perlu ekstraksi embedding ulang.

#### `get_temporary_embedding(check_id)`

Mengambil temporary embedding berdasarkan `check_id`.

Jika data expired, cleanup dilakukan lebih dulu.

#### `delete_temporary_embedding(check_id)`

Menghapus temporary embedding.

Dipakai setelah:
- metadata berhasil diregistrasi;
- data tidak lagi dibutuhkan.

#### `review_temporary_embedding(check_id, approved, reason)`

Mengubah status review manual pada temporary embedding.

Alasannya:
- `review_required` bisa berubah menjadi boleh register setelah disetujui reviewer.

### Client Service di Folder `services/`

#### `feature_client.get_embedding(image_bytes)`

Memanggil feature extraction service.

Return:
- `clip_embedding`;
- `cnn_embedding`.

#### `web_search_client.send_to_web_search(file_bytes)`

Memanggil web search service untuk mencari kandidat eksternal.

#### `similarity_client.send_to_similarity(...)`

Mengirim embedding query dan kandidat eksternal ke similarity-check service.

Return:
- overall score;
- best match;
- top internal/external/combined.

#### `decision_client.send_to_decision(...)`

Mengirim skor ke decision engine.

Return:
- status keputusan;
- risk level;
- requires review;
- reason.

#### `metadata_client.create_metadata(metadata)`

Membuat metadata di copyright-metadata-service.

#### `metadata_client.update_embedding_reference(metadata_id, embedding_reference)`

Mengupdate metadata dengan referensi Milvus setelah embedding berhasil disimpan.

#### `embedding_client.insert_embedding(metadata_id, feature, embedding_version)`

Menyimpan embedding ke Milvus melalui similarity-check service.

#### `cloudinary_client.upload_image(file_bytes, public_id)`

Upload gambar final ke Cloudinary.

#### `cloudinary_client.delete_image(public_id)`

Hapus gambar dari Cloudinary.

### `schemas/response_schema.py`

Class di file ini mendefinisikan bentuk response upload.

Alasannya:
- response upload cukup kompleks;
- schema membantu menjaga struktur response agar konsisten.
