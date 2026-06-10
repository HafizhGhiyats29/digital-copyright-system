# Copyright Metadata Service

Service ini menyimpan metadata karya hak cipta dan referensi embedding yang dipakai untuk integrasi Milvus. Storage dapat memakai JSON lokal untuk pengujian atau MongoDB untuk mode utama.

## Peran Service

- Menyimpan metadata karya, seperti `check_id`, judul, deskripsi, kategori, dan URL gambar.
- Menyimpan referensi ke embedding di Milvus melalui `milvus_collection` dan `milvus_id`.
- Menyimpan status embedding: `pending`, `ready`, atau `failed`.
- Menjadi sumber detail metadata saat similarity search mengembalikan ID dari Milvus.
- Mencegah registrasi ganda dengan `check_id`.

## Data Model

Field utama metadata:

```json
{
  "id": "uuid-generated-by-service",
  "check_id": "uuid-hasil-pengecekan",
  "title": "Serwataka Toguri Sharpie",
  "description": "Deskripsi karya",
  "category": "HAK CIPTA",
  "sub_category": "Karya Seni",
  "copyright_category": "Karya Seni",
  "copyright_sub_category": "Seni Ilustrasi",
  "image_url": "https://example.com/image.jpg",
  "cloudinary_public_id": "copyright/serwataka",
  "milvus_collection": "copyright_embeddings",
  "milvus_id": "uuid-generated-by-service",
  "embedding_version": "clip-cnn-v1",
  "embedding_status": "pending",
  "created_at": "2026-05-18T00:00:00+00:00",
  "updated_at": "2026-05-18T00:00:00+00:00"
}
```

Catatan:

- `check_id` adalah ID hasil pengecekan plagiarisme dan dipakai sebagai anti-duplikasi registrasi.
- `ki_id` dan `ki_uuid` bersifat opsional untuk integrasi database KI resmi di masa depan.
- `id` adalah ID utama metadata yang dibuat otomatis oleh service.
- `milvus_id` adalah ID row/vector di Milvus.
- Jika satu row Milvus menyimpan `clip_embedding` dan `cnn_embedding`, cukup pakai satu `milvus_id`.
- Detail seperti `title`, `image_url`, dan kategori tetap disimpan di service ini, bukan di Milvus.

## Endpoint Langsung

Jalankan service di port `8006`:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8006
```

Endpoint:

```text
GET    /health
POST   /metadata
GET    /metadata
GET    /metadata/{metadata_id}
PUT    /metadata/{metadata_id}
PATCH  /metadata/{metadata_id}/embedding
DELETE /metadata/{metadata_id}
```

## Endpoint Lewat API Gateway

Jika API Gateway berjalan di port `8080`, endpoint metadata tersedia di:

```text
POST   /api/v1/metadata
GET    /api/v1/metadata
GET    /api/v1/metadata/{metadata_id}
PUT    /api/v1/metadata/{metadata_id}
PATCH  /api/v1/metadata/{metadata_id}/embedding
DELETE /api/v1/metadata/{metadata_id}
```

Swagger Gateway:

```text
http://127.0.0.1:8080/docs
```

## Contoh Create Metadata

```json
{
  "check_id": "uuid-hasil-pengecekan",
  "title": "Serwataka Toguri Sharpie",
  "description": "Contoh deskripsi karya",
  "category": "HAK CIPTA",
  "sub_category": "Karya Seni",
  "copyright_category": "Karya Seni",
  "copyright_sub_category": "Seni Ilustrasi",
  "image_url": null,
  "cloudinary_public_id": null,
  "milvus_collection": null,
  "milvus_id": null,
  "embedding_version": null,
  "embedding_status": "pending"
}
```

## Contoh Update Embedding

Endpoint ini dipakai setelah embedding berhasil dibuat dan disimpan ke Milvus.

```text
PATCH /metadata/{metadata_id}/embedding
```

Body:

```json
{
  "milvus_collection": "copyright_embeddings",
  "milvus_id": "metadata-id-yang-sama-atau-id-row-milvus",
  "embedding_version": "clip-cnn-v1",
  "embedding_status": "ready"
}
```

Jika embedding gagal:

```json
{
  "embedding_status": "failed"
}
```

## Alur Integrasi Milvus Nanti

Rencana alur cek dan registrasi karya:

```text
1. User upload gambar ke upload-service untuk dicek.
2. Feature extraction membuat CLIP dan CNN embedding sementara.
3. Similarity service dan decision engine mengecek indikasi plagiarisme.
4. Upload-service mengembalikan check_id, can_register, registration_status, dan registration_reason.
5. Jika can_register = false, metadata tidak boleh ditambahkan.
6. Jika can_register = true, embedding sementara dari check_id boleh dipromosikan ke Milvus.
7. Metadata karya dibuat di copyright-metadata-service.
8. Service pemroses menyimpan embedding sementara ke Milvus.
9. Service pemroses memanggil PATCH /metadata/{id}/embedding.
10. Metadata berubah dari pending menjadi ready.
```

Contoh response ringkas dari upload-service:

```json
{
  "status": "processed",
  "check_id": "uuid-hasil-cek",
  "can_register": true,
  "registration_status": "allowed",
  "registration_reason": "Registrasi diizinkan karena tidak ada indikasi plagiarisme yang perlu ditinjau."
}
```

Jika `can_register = true`, metadata sebaiknya didaftarkan lewat endpoint orkestrasi upload-service:

```text
POST /register-metadata
```

atau lewat API Gateway:

```text
POST /api/v1/register-metadata
```

Body:

```json
{
  "check_id": "uuid-hasil-cek",
  "title": "Serwataka Toguri Sharpie",
  "description": "Contoh deskripsi karya",
  "category": "HAK CIPTA",
  "sub_category": "Karya Seni",
  "copyright_category": "Karya Seni",
  "copyright_sub_category": "Seni Ilustrasi",
  "image_url": "https://example.com/image.jpg",
  "cloudinary_public_id": null
}
```

Endpoint ini akan menolak registrasi jika `check_id` tidak ditemukan, kedaluwarsa, atau hasil decision masih mengindikasikan plagiarisme/review.

Jika hasil awal adalah `review_required`, reviewer dapat memberi keputusan manual:

```text
POST /api/v1/review-check/{check_id}/approve
POST /api/v1/review-check/{check_id}/reject
```

Contoh approval:

```json
{
  "reason": "Kemiripan hanya pada ide umum, bukan ekspresi visual yang sama."
}
```

Setelah `approve`, `check_id` tersebut bisa dipakai di `POST /api/v1/register-metadata`. Setelah `reject`, registrasi tetap ditolak.

Aturan registrasi:

```text
high_similarity      -> blocked
medium_similarity    -> review_required
low_similarity       -> allowed
no_significant_similarity -> allowed
```

Catatan: metadata service tidak melakukan embedding. Embedding tetap dibuat oleh feature-extraction-service saat proses upload/check, lalu hanya disimpan permanen ke Milvus jika hasil pengecekan aman.

Rencana alur similarity search:

```text
1. Query image dibuat embedding.
2. Similarity service mencari embedding terdekat di Milvus.
3. Milvus mengembalikan milvus_id atau metadata_id.
4. Sistem mengambil detail karya dari copyright-metadata-service.
5. Decision engine membuat keputusan berdasarkan score.
```

## Menjalankan Test

Install dependency:

```powershell
python -m pip install -r requirements.txt
```

Jalankan test:

```powershell
python -m pytest tests/test_metadata.py -q
```

Ekspektasi hasil:

```text
2 passed
```

Test memakai file JSON sementara di folder `tests`, sehingga tidak mengubah `data/metadata.json`.
# Copyright Metadata Service - Panduan Memahami Kode

Service ini menyimpan data metadata karya cipta. Metadata disimpan di MongoDB, sedangkan gambar disimpan di Cloudinary dan embedding disimpan di Milvus. Service ini menyimpan referensi ke keduanya.

## Tanggung Jawab Utama

- Menyediakan CRUD metadata.
- Menyimpan metadata ke MongoDB.
- Mendukung fallback storage JSON untuk development.
- Menyimpan referensi Cloudinary.
- Menyimpan referensi vector Milvus.
- Mencegah duplikasi metadata berdasarkan `check_id`.
- Menyediakan endpoint update status embedding.

## File Penting

### `app.py`

Entry point FastAPI metadata service.

Endpoint penting:
- `POST /metadata`: membuat metadata.
- `GET /metadata`: mengambil daftar metadata.
- `GET /metadata/{id}`: mengambil metadata detail.
- `PUT /metadata/{id}`: update metadata.
- `DELETE /metadata/{id}`: hapus metadata.
- endpoint embedding update untuk mengisi `milvus_collection`, `milvus_id`, dan `embedding_status`.

Alasannya:
- Metadata service hanya fokus pada data deskriptif.
- Operasi Cloudinary dan Milvus biasanya diorkestrasi oleh upload service atau API Gateway.

### `models/metadata_model.py`

Berisi schema Pydantic untuk metadata.

Field penting:
- `id`: ID internal metadata.
- `check_id`: ID hasil pengecekan plagiarisme.
- `title`, `description`, dan kategori karya.
- `image_url`: URL gambar dari Cloudinary.
- `cloudinary_public_id`: ID file di Cloudinary.
- `milvus_collection`: nama collection vector.
- `milvus_id`: ID vector di Milvus.
- `embedding_version`: versi embedding.
- `embedding_status`: status embedding, misalnya `pending` atau `ready`.

Catatan:
- `ki_id` dan `ki_uuid` dibuat opsional karena saat ini berasal dari sistem lain dan belum menjadi sumber utama.
- Untuk data baru, sistem bisa berjalan tanpa dua field tersebut.

Alasannya:
- Metadata harus tetap bisa dibuat walaupun belum terhubung dengan sistem KI eksternal.
- Field referensi vector dan object storage membuat metadata bisa menghubungkan MongoDB, Milvus, dan Cloudinary.

### `services/metadata_store.py`

Berisi logic penyimpanan metadata.

Tugas utama:
- koneksi ke MongoDB,
- membuat index,
- menyimpan metadata,
- mengambil daftar metadata,
- update metadata,
- delete metadata,
- fallback ke JSON jika mode development membutuhkan,
- mengecek duplikasi berdasarkan `check_id`.

Alasannya:
- Semua akses storage dikumpulkan di satu file.
- Jika nanti storage diganti atau dioptimasi, router tidak perlu banyak berubah.

Duplikasi:
- `check_id` dipakai agar satu hasil cek plagiarisme tidak bisa dipakai berkali-kali untuk membuat metadata.
- Jika `check_id` sudah ada, service mengembalikan error conflict.

### `utils/metrics.py`

Berisi helper metric sederhana.

Alasannya:
- Berguna untuk observability dasar.
- Bisa diperluas jika nanti service memakai monitoring.

### `utils/internal_auth.py`

Memvalidasi internal API key.

Alasannya:
- Metadata service tidak seharusnya dipanggil sembarang client secara langsung.
- Service internal seperti API Gateway dan upload service harus membawa API key yang benar.

## Alur Registrasi Metadata

1. User melakukan cek plagiarisme melalui upload service.
2. Upload service mendapat `check_id`.
3. Jika hasil aman, user mengisi metadata.
4. Upload service mengirim metadata ke service ini.
5. Metadata disimpan ke MongoDB.
6. Upload service menyimpan embedding ke Milvus.
7. Metadata di-update dengan `milvus_id` dan `embedding_status = ready`.

## Alasan MongoDB Dipakai

MongoDB cocok untuk metadata karena:

- struktur dokumen fleksibel,
- field metadata dapat berkembang,
- mudah menyimpan data nested atau optional,
- cocok untuk CRUD administratif.

Milvus tidak dipakai untuk metadata karena Milvus fokus pada pencarian vector, bukan data deskriptif.

## Catatan Desain

Service ini tidak menyimpan file gambar dan tidak menghitung embedding. Tugasnya adalah menjadi sumber kebenaran untuk data metadata karya. File gambar berada di Cloudinary, sedangkan vector berada di Milvus.

## Penjelasan Kode Per Fungsi

### `app.py`

#### `health()`

Endpoint health check.

Alasannya:
- memastikan metadata service aktif.

#### `root()`

Endpoint root sederhana.

Biasanya dipakai untuk cek manual bahwa service dapat diakses.

#### `migrate_json_metadata_to_mongodb()`

Endpoint migrasi dari storage JSON ke MongoDB.

Alur:
1. Membaca metadata dari JSON.
2. Memasukkan data ke MongoDB.
3. Mengembalikan ringkasan migrasi.

Alasannya:
- awal development bisa memakai JSON;
- saat siap, data bisa dipindahkan ke MongoDB.

#### `create(data: MetadataCreate)`

Membuat metadata baru.

Alur:
1. Validasi body dengan `MetadataCreate`.
2. Kirim data ke `create_metadata`.
3. Jika `check_id` duplikat, return conflict.
4. Return metadata yang sudah dibuat.

Alasannya:
- metadata baru harus melewati service store agar storage JSON/MongoDB tetap konsisten.

#### `read_all()`

Mengambil semua metadata.

#### `read_by_id(metadata_id: str)`

Mengambil satu metadata berdasarkan ID.

Jika tidak ditemukan:
- return 404.

#### `update(metadata_id: str, data: MetadataUpdate)`

Update metadata parsial.

Alur:
1. Ambil field yang dikirim saja.
2. Jika body kosong, return 400.
3. Update data di storage.
4. Jika ID tidak ditemukan, return 404.

Alasannya:
- update tidak wajib mengirim semua field.
- body kosong dianggap request tidak valid.

#### `update_embedding_reference(metadata_id: str, data: EmbeddingReferenceUpdate)`

Mengupdate referensi Milvus pada metadata.

Field yang biasanya diupdate:
- `milvus_collection`;
- `milvus_id`;
- `embedding_version`;
- `embedding_status`.

Alasannya:
- metadata dibuat lebih dulu;
- embedding disimpan ke Milvus setelah metadata punya ID;
- referensi vector perlu ditulis kembali ke metadata.

#### `delete(metadata_id: str)`

Menghapus metadata berdasarkan ID.

Catatan:
- endpoint ini hanya menghapus metadata;
- cleanup Cloudinary dan Milvus biasanya diorkestrasi oleh API Gateway.

### `models/metadata_model.py`

#### `MetadataBase`

Schema dasar metadata.

Berisi field umum seperti:
- `check_id`;
- `title`;
- `description`;
- kategori;
- `image_url`;
- `cloudinary_public_id`;
- referensi Milvus.

Alasannya:
- field yang sama bisa dipakai oleh create dan response.

#### `MetadataCreate`

Schema untuk create metadata.

Turunan dari `MetadataBase`.

Alasannya:
- request create memakai struktur dasar metadata.

#### `MetadataUpdate`

Schema untuk update parsial.

Semua field opsional.

Alasannya:
- user dapat mengubah satu atau beberapa field saja.

#### `EmbeddingReferenceUpdate`

Schema khusus update referensi embedding.

Alasannya:
- update embedding punya kebutuhan khusus dan tidak perlu membuka semua field metadata.

#### `MetadataResponse`

Schema response metadata.

Tambahan:
- `id`;
- `created_at`;
- `updated_at`.

Alasannya:
- response perlu membawa field hasil generate dari sistem.

### `services/metadata_store.py`

#### `DuplicateMetadataError`

Error khusus ketika `check_id` sudah pernah dipakai.

Alasannya:
- satu hasil cek plagiarisme tidak boleh membuat banyak metadata.

#### `_load_settings()`

Membaca konfigurasi metadata service.

#### `_storage_type()`

Menentukan storage aktif: JSON atau MongoDB.

Alasannya:
- service bisa fleksibel untuk development dan production.

#### `_now_iso()`

Menghasilkan timestamp ISO.

Dipakai untuk:
- `created_at`;
- `updated_at`.

#### `_ensure_store()`

Memastikan file/folder JSON store tersedia.

Alasannya:
- fallback JSON tidak error saat file belum ada.

#### `_read_all_json()` dan `_write_all_json(items)`

Membaca dan menulis semua metadata pada storage JSON.

Alasannya:
- mode JSON sederhana dan cocok untuk development awal.

#### `_mongo_settings()`

Mengambil konfigurasi MongoDB.

#### `_get_mongo_collection()`

Membuka collection MongoDB dan memastikan index penting tersedia.

Index penting:
- unique index untuk `id`;
- partial unique index untuk `check_id`.

Alasannya:
- `id` harus unik;
- `check_id` mencegah duplikasi registrasi.

#### `_normalize_mongo_item(item)`

Membersihkan item MongoDB sebelum dikirim sebagai response.

Biasanya:
- menghapus atau mengubah `_id` ObjectId agar JSON serializable.

#### `_create_metadata_json(data)`

Membuat metadata di JSON store.

Logika:
- cek duplikasi `check_id`;
- generate `id`;
- isi timestamp;
- simpan ke file JSON.

#### `_get_all_metadata_json()`

Mengambil semua metadata dari JSON.

#### `_get_metadata_by_id_json(metadata_id)`

Mengambil metadata dari JSON berdasarkan ID.

#### `_update_metadata_json(metadata_id, data)`

Update metadata JSON.

Logika:
- cari item berdasarkan ID;
- merge field baru;
- update `updated_at`;
- tulis ulang file.

#### `_delete_metadata_json(metadata_id)`

Menghapus metadata dari JSON.

#### `_create_metadata_mongo(data)`

Membuat metadata di MongoDB.

Logika:
- cek duplikasi `check_id`;
- generate `id`;
- isi timestamp;
- insert ke MongoDB.

#### `_get_all_metadata_mongo()`

Mengambil semua metadata dari MongoDB.

#### `_get_metadata_by_id_mongo(metadata_id)`

Mengambil metadata MongoDB berdasarkan ID.

#### `_update_metadata_mongo(metadata_id, data)`

Update metadata MongoDB.

Logika:
- set field yang dikirim;
- update `updated_at`;
- return data terbaru.

#### `_delete_metadata_mongo(metadata_id)`

Menghapus metadata dari MongoDB.

#### `create_metadata(data)`

Facade create metadata.

Fungsi ini memilih JSON atau MongoDB berdasarkan konfigurasi.

Alasannya:
- router tidak perlu tahu storage yang sedang aktif.

#### `get_all_metadata()`

Facade list metadata.

#### `get_metadata_by_id(metadata_id)`

Facade detail metadata.

#### `update_metadata(metadata_id, data)`

Facade update metadata.

#### `delete_metadata(metadata_id)`

Facade delete metadata.

#### `migrate_json_to_mongodb()`

Memindahkan data JSON ke MongoDB.

Alasannya:
- transisi dari development storage ke database bisa dilakukan tanpa menulis script terpisah.

#### `check_storage_health()`

Mengecek kondisi storage aktif.

Alasannya:
- membantu debugging apakah service memakai JSON atau MongoDB dan apakah storage dapat diakses.

### `utils/internal_auth.py`

Fungsi-fungsinya sama dengan service lain:

- `_load_env_file`;
- `get_internal_api_key`;
- `internal_auth_headers`;
- `require_internal_api_key`.

Tujuannya:
- melindungi metadata service dari akses langsung tanpa API key internal.
