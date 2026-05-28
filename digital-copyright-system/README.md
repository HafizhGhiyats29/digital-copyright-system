# Digital Copyright System

Sistem ini digunakan untuk memeriksa kemiripan gambar karya, mengambil keputusan risiko plagiarisme, lalu menyimpan metadata dan embedding karya yang lolos verifikasi.

## Arsitektur Singkat

```text
Frontend
  -> API Gateway
    -> Upload Service
      -> Feature Extraction Service
      -> Web Search Service
      -> Similarity Check Service
      -> Decision Engine
      -> Copyright Metadata Service
      -> Cloudinary
      -> Milvus
      -> MongoDB
```

Peran penyimpanan:

- Cloudinary: menyimpan file gambar karya.
- MongoDB: menyimpan metadata karya.
- Milvus: menyimpan embedding CLIP dan CNN.
- MinIO: object storage internal untuk Milvus.

## Panduan Kode Per Service

Setiap service memiliki README sendiri yang menjelaskan fungsi file, alur logika, dan alasan desain kodenya:

- `api-gateway/README.md`: proxy, CORS, internal API key, dan cleanup lintas-service.
- `upload-service/README.md`: orkestrasi upload, pengecekan plagiarisme, review manual, dan registrasi metadata.
- `feature-extraction-service/README.md`: preprocessing gambar serta ekstraksi embedding CLIP dan CNN.
- `web-search-service/README.md`: pencarian kandidat eksternal dari web.
- `similarity-check-service/README.md`: cosine similarity, Milvus, dan penggabungan skor internal/eksternal.
- `decision-engine/README.md`: preset threshold, score rules, dan keputusan registrasi.
- `copyright-metadata-service/README.md`: CRUD metadata, MongoDB, anti-duplikasi `check_id`, dan referensi Cloudinary/Milvus.

## Alur Cek dan Registrasi

1. User upload gambar dari frontend.
2. API Gateway meneruskan request ke `upload-service`.
3. `upload-service` mengekstrak embedding CLIP dan CNN.
4. Sistem melakukan pencarian kemiripan internal dari Milvus dan eksternal dari web search.
5. `decision-engine` memberi status keputusan.
6. Response upload mengembalikan `check_id`.
7. Jika hasil aman, user dapat mendaftarkan metadata memakai `check_id`.
8. `check_id` disimpan pada metadata dan menjadi tiket sekali pakai untuk mencegah registrasi ganda.
9. Gambar disimpan ke Cloudinary.
10. Embedding sementara dipromosikan ke Milvus.
11. Metadata menyimpan referensi `milvus_collection`, `milvus_id`, dan `embedding_status`.

## Status Registrasi

```text
allowed          -> metadata dapat didaftarkan
review_required  -> butuh approval manual
blocked          -> metadata tidak boleh didaftarkan
```

Jika `review_required`, reviewer dapat memanggil:

```text
POST /api/v1/review-check/{check_id}/approve
POST /api/v1/review-check/{check_id}/reject
```

Setelah `approve`, `check_id` dapat dipakai untuk `POST /api/v1/register-metadata`.

## Identitas Data

| Field | Fungsi |
|---|---|
| `check_id` | ID hasil pengecekan plagiarisme, dipakai sebagai anti-duplikasi registrasi |
| `id` | ID internal metadata, dipakai untuk CRUD |
| `milvus_id` | ID vector/row embedding di Milvus |
| `ki_id` / `ki_uuid` | Referensi opsional untuk database KI resmi di masa depan |

Catatan: `ki_id` dan `ki_uuid` tidak ditampilkan di frontend dan tidak wajib dikirim. Field ini hanya disiapkan untuk integrasi eksternal nanti.

## Endpoint Utama

API Gateway berjalan di:

```text
http://localhost:8080/docs
```

Endpoint utama:

```text
POST   /api/v1/upload
POST   /api/v1/register-metadata
POST   /api/v1/review-check/{check_id}/approve
POST   /api/v1/review-check/{check_id}/reject
GET    /api/v1/metadata
GET    /api/v1/metadata/{metadata_id}
PUT    /api/v1/metadata/{metadata_id}
DELETE /api/v1/metadata/{metadata_id}
```

## Validasi Upload

Frontend dan backend sama-sama membatasi upload gambar:

- Format: JPG, PNG, WEBP.
- Ukuran maksimal: 10 MB.
- Backend juga memvalidasi isi gambar memakai Pillow.
- Total resolusi dibatasi maksimal 40 juta piksel.

Validasi frontend hanya untuk kenyamanan user. Validasi final tetap dilakukan di backend.

## Menjalankan Dengan Docker

Pastikan file `.env` sudah tersedia di root project.

Jalankan semua service:

```bash
docker compose up -d --build
```

Rebuild service tertentu setelah perubahan kode:

```bash
docker compose up -d --build api-gateway upload-service copyright-metadata-service
```

Jangan gunakan `docker compose down -v` kecuali memang ingin menghapus volume data MongoDB/Milvus.

## Environment Penting

Secret dan konfigurasi environment disimpan di `.env`, bukan di `settings.yaml`.

Contoh:

```env
SERPAPI_KEY=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
CLOUDINARY_FOLDER=copyright-registrations
INTERNAL_API_KEY=
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

`settings.yaml` dipakai untuk default konfigurasi lokal. `.env` dipakai untuk override sesuai environment.

## Catatan Keamanan

- Frontend hanya mengakses API Gateway.
- Service internal dilindungi `X-Internal-API-Key`.
- Mutasi metadata, review, upload embedding, dan delete dilakukan melalui gateway/service internal.
- Untuk deployment publik, batasi `CORS_ALLOW_ORIGINS` ke domain frontend yang benar.
