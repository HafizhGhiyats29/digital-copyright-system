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
possible_plagiarism  -> review_required
medium_similarity    -> review_required
low_similarity       -> allowed
no_significant       -> allowed
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
