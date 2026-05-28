# Digital Copyright System

Digital Copyright System adalah sistem microservice untuk mengecek kemiripan gambar karya sebelum metadata hak cipta didaftarkan. Sistem mengekstrak embedding gambar menggunakan CLIP dan CNN, mencari kandidat kemiripan internal dan eksternal, mengambil keputusan risiko plagiarisme, lalu menyimpan metadata dan embedding karya yang lolos .

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Arsitektur](#arsitektur)
- [Struktur Folder](#struktur-folder)
- [Identitas Data](#identitas-data)
- [Alur Sistem](#alur-sistem)
- [Validasi Upload](#validasi-upload)
- [Konfigurasi](#konfigurasi)
- [Menjalankan Dengan Docker](#menjalankan-dengan-docker)
- [Menjalankan Frontend](#menjalankan-frontend)
- [Endpoint Utama](#endpoint-utama)
- [Evaluasi Similarity](#evaluasi-similarity)
- [Catatan Keamanan](#catatan-keamanan)

## Fitur Utama

- Upload gambar untuk cek indikasi plagiarisme.
- Validasi gambar JPG, PNG, dan WEBP.
- Ekstraksi fitur gambar:
  - CLIP embedding untuk konteks visual.
  - CNN embedding untuk detail visual.
- Reverse image search eksternal menggunakan SerpAPI.
- Pencarian internal menggunakan Milvus.
- Metadata disimpan di MongoDB.
- Gambar karya disimpan di Cloudinary.
- Decision engine dengan preset threshold `strict`, `balanced`, dan `sensitive`.
- Review manual untuk hasil yang berada di area abu-abu.
- Registrasi metadata hanya bisa dilakukan dengan `check_id` hasil pengecekan.
- Anti-duplikasi registrasi metadata berbasis `check_id`.
- API Gateway sebagai pintu masuk utama.

## Arsitektur

```text
Frontend
  |
  v
API Gateway :8080
  |
  v
Upload Service :8000
  |
  +--> Feature Extraction Service :8002
  |      - CLIP embedding
  |      - CNN embedding
  |
  +--> Web Search Service :8001
  |      - Upload sementara ke Cloudinary
  |      - Reverse image search via SerpAPI
  |      - Embedding kandidat eksternal
  |
  +--> Similarity Check Service :8003
  |      - Similarity internal ke Milvus
  |      - Similarity eksternal dengan cosine similarity
  |
  +--> Decision Engine :8005
  |      - Menentukan allowed / review_required / blocked
  |
  +--> Copyright Metadata Service :8006
         - Metadata MongoDB
         - Referensi vector Milvus
```

Storage yang digunakan:

| Storage | Fungsi |
|---|---|
| Cloudinary | Menyimpan file gambar karya |
| MongoDB | Menyimpan metadata karya |
| Milvus | Menyimpan embedding CLIP dan CNN |
| MinIO | Object storage internal untuk Milvus |

## Struktur Folder

```text
Capstone2/
  README.md
  digital-copyright-system/
    api-gateway/
    upload-service/
    feature-extraction-service/
    web-search-service/
    similarity-check-service/
    decision-engine/
    copyright-metadata-service/
    database/
      mongodb/
      milvus/
    evaluation_dataset/
    scripts/
    reports/
  ../Capstone website/Frontend_CD/
```

Backend utama berada di:

```text
digital-copyright-system/
```

Frontend berada di:

```text
E:\Hafizh Code\Capstone website\Frontend_CD
```

## Identitas Data

| Field | Fungsi |
|---|---|
| `check_id` | ID hasil pengecekan plagiarisme. Dipakai sebagai tiket sekali pakai untuk registrasi metadata. |
| `id` | ID internal metadata. Dipakai untuk CRUD metadata. |
| `milvus_id` | ID vector/row embedding di Milvus. |
| `ki_id` / `ki_uuid` | Referensi opsional untuk database KI resmi di masa depan. Tidak ditampilkan di frontend dan tidak wajib dikirim. |

Catatan penting:

- `check_id` mencegah satu hasil pengecekan didaftarkan berkali-kali.
- `id` tidak cocok untuk anti-duplikasi karena selalu dibuat baru saat metadata dibuat.
- `ki_id` dan `ki_uuid` tidak dipakai dulu karena sumbernya dari database eksternal.

## Alur Sistem

### 1. Cek Plagiarisme

```text
User upload gambar
  -> Upload Service membuat check_id
  -> Feature Extraction membuat CLIP dan CNN embedding
  -> Web Search mencari kandidat eksternal
  -> Similarity Check mencari kandidat internal dan eksternal
  -> Decision Engine menentukan status
  -> Response dikirim ke frontend
```

Status registrasi:

| Status | Arti |
|---|---|
| `allowed` | Metadata boleh didaftarkan |
| `review_required` | Perlu review manual |
| `blocked` | Metadata tidak boleh didaftarkan |

### 2. Review Manual

Jika status `review_required`, reviewer bisa memilih:

```text
POST /api/v1/review-check/{check_id}/approve
POST /api/v1/review-check/{check_id}/reject
```

Jika disetujui, `check_id` dapat dipakai untuk registrasi metadata.

### 3. Registrasi Metadata

Registrasi metadata dilakukan melalui:

```text
POST /api/v1/register-metadata
```

Contoh body:

```json
{
  "check_id": "uuid-hasil-cek",
  "title": "Judul Karya",
  "description": "Deskripsi karya",
  "category": "HAK CIPTA",
  "sub_category": "karya seni",
  "copyright_category": "karya seni",
  "copyright_sub_category": "karya ilustrasi"
}
```

Saat berhasil:

- Metadata disimpan ke MongoDB.
- Gambar disimpan ke Cloudinary.
- Embedding sementara dipromosikan ke Milvus.
- Metadata menyimpan referensi `milvus_collection`, `milvus_id`, `embedding_version`, dan `embedding_status`.

Jika `check_id` yang sama digunakan lagi, sistem menolak dengan `409 Conflict`.

## Validasi Upload

Frontend dan backend membatasi upload:

- Format: JPG, PNG, WEBP.
- Ukuran maksimal: 10 MB.
- Backend memvalidasi isi gambar dengan Pillow.
- Total piksel maksimal: 40 juta piksel.

Validasi frontend hanya untuk pengalaman user. Validasi utama tetap berada di backend.

## Konfigurasi

Gunakan `.env` untuk secret dan konfigurasi environment.

File contoh:

```text
digital-copyright-system/.env.example
```

Contoh isi:

```env
SERPAPI_KEY=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
CLOUDINARY_FOLDER=copyright-registrations
INTERNAL_API_KEY=
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Prinsip konfigurasi:

- `settings.yaml` untuk default lokal yang aman masuk Git.
- `.env` untuk secret dan override environment.
- Jangan commit `.env` berisi key asli.

## Menjalankan Dengan Docker

Masuk ke folder backend:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system"
```

Jalankan semua service:

```powershell
docker compose up -d --build
```

Rebuild service tertentu setelah perubahan kode:

```powershell
docker compose up -d --build api-gateway upload-service copyright-metadata-service
```

Matikan container tanpa menghapus data:

```powershell
docker compose down
```

Jangan gunakan ini kecuali ingin menghapus volume/data:

```powershell
docker compose down -v
```

API Gateway dapat diakses dari host melalui:

```text
http://localhost:8080/docs
```

Walaupun service berjalan di Docker, browser tetap memakai `localhost`, bukan nama service Docker seperti `api-gateway`.

## Menjalankan Frontend

Masuk ke folder frontend:

```powershell
cd "E:\Hafizh Code\Capstone website\Frontend_CD"
```

Pastikan `.env` frontend berisi:

```env
VITE_API_BASE_URL=http://localhost:8080/api/v1
```

Install dependency:

```powershell
npm install
```

Jalankan frontend:

```powershell
npm run dev
```

Build frontend:

```powershell
npm.cmd run build
```

Jika PowerShell menolak `npm` karena execution policy, gunakan `npm.cmd`.

## Endpoint Utama

Base URL:

```text
http://localhost:8080
```

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/health` | Health check gateway |
| POST | `/api/v1/upload` | Upload dan cek plagiarisme |
| POST | `/api/v1/register-metadata` | Registrasi metadata memakai `check_id` |
| POST | `/api/v1/review-check/{check_id}/approve` | Approve hasil review manual |
| POST | `/api/v1/review-check/{check_id}/reject` | Reject hasil review manual |
| GET | `/api/v1/metadata` | List metadata |
| GET | `/api/v1/metadata/{metadata_id}` | Detail metadata |
| PUT | `/api/v1/metadata/{metadata_id}` | Update metadata |
| DELETE | `/api/v1/metadata/{metadata_id}` | Hapus metadata, vector Milvus, dan gambar Cloudinary |

## Evaluasi Similarity

Dataset evaluasi berada di:

```text
digital-copyright-system/evaluation_dataset
```

Script evaluasi:

```text
digital-copyright-system/scripts/evaluate_similarity.py
```

Jalankan:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system"
python .\scripts\evaluate_similarity.py
```

Hasil evaluasi berada di:

```text
digital-copyright-system/reports/similarity_evaluation.csv
```

Metrik yang dicatat:

- Accuracy
- Precision
- Recall
- F1
- True Positive
- False Positive
- False Negative
- True Negative

## Catatan Keamanan

- Frontend hanya mengakses API Gateway.
- Service internal dilindungi header `X-Internal-API-Key`.
- Direct access ke service internal sebaiknya tidak dibuka ke publik.
- CORS API Gateway harus dibatasi ke domain frontend.
- Secret disimpan di `.env`, bukan `settings.yaml`.
- Untuk user internal, role user belum wajib, tetapi endpoint mutasi tetap lewat gateway.

## Dokumentasi Tambahan

Dokumentasi backend lebih detail:

```text
digital-copyright-system/README.md
```

Dokumentasi metadata service:

```text
digital-copyright-system/copyright-metadata-service/README.md
```

Dokumentasi frontend:

```text
E:\Hafizh Code\Capstone website\Frontend_CD\README.md
```

