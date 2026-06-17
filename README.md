# Digital Copyright System

Digital Copyright System adalah sistem microservice untuk mengecek kemiripan gambar karya sebelum metadata hak cipta didaftarkan. Sistem mengekstrak embedding gambar menggunakan CLIP dan CNN, mencari kandidat kemiripan internal dan eksternal, mengambil keputusan risiko plagiarisme, lalu menyimpan metadata, gambar, report pemeriksaan, dan referensi embedding karya yang lolos verifikasi.

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [System Requirements](#system-requirements)
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

## System Requirements

Kebutuhan minimum yang disarankan untuk menjalankan sistem secara lokal:

| Komponen | Kebutuhan |
|---|---|
| OS | Windows 10/11 64-bit, Linux, atau macOS |
| Python | Python 3.10 atau 3.11 |
| Node.js | Node.js 18+ |
| Package manager frontend | `npm` atau `pnpm` |
| Docker | Docker Desktop dengan Docker Compose |
| RAM | Minimal 16 GB, disarankan 32 GB untuk model CLIP/CNN |
| Disk kosong | Minimal 15-20 GB, disarankan lebih besar jika memakai Docker |
| GPU | Opsional. CUDA dapat mempercepat feature extraction |

Kebutuhan layanan eksternal:

| Layanan | Fungsi |
|---|---|
| SerpAPI | Reverse image search / Google Lens |
| Cloudinary | Object storage gambar karya dan gambar sementara untuk web search |
| MongoDB | Database metadata karya |
| Milvus | Vector database untuk embedding internal |
| MinIO | Object storage internal untuk Milvus |

Kebutuhan Python utama per backend:

- `fastapi`
- `uvicorn`
- `pydantic`
- `httpx`
- `pymongo`
- `pymilvus`
- `Pillow`
- `numpy`
- `torch`
- `torchvision`
- `transformers`

Kebutuhan frontend utama:

- React
- Vite
- Tailwind CSS
- Axios atau HTTP client sejenis

Catatan:

- Jika menjalankan seluruh service memakai Docker, pastikan Docker Desktop memiliki ruang disk cukup.
- Model CLIP dan ResNet50 dapat mengunduh bobot model saat pertama kali dijalankan.
- Jika preprocessing gambar berubah, embedding lama di Milvus perlu dibuat ulang agar hasil similarity konsisten.

## Fitur Utama

- Upload gambar untuk cek indikasi plagiarisme.
- Validasi gambar JPG, PNG, dan WEBP.
- Ekstraksi fitur gambar:
  - CLIP embedding untuk konteks visual.
  - CNN embedding untuk detail visual.
- Reverse image search eksternal menggunakan SerpAPI.
- Kandidat eksternal diprioritaskan memakai URL gambar asli dari SerpAPI, lalu fallback ke thumbnail jika gambar asli gagal diunduh.
- Pencarian internal menggunakan Milvus.
- Metadata disimpan di MongoDB.
- Gambar karya disimpan di Cloudinary.
- Report hasil pengecekan disimpan bersama metadata tanpa menyimpan array embedding mentah.
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

Catatan embedding:

- MongoDB hanya menyimpan metadata, report, dan referensi vector.
- Array `clip_embedding` dan `cnn_embedding` tidak disimpan di MongoDB report.
- Vector embedding karya yang lolos disimpan di Milvus.

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
     -> mencoba gambar asli dari SerpAPI
     -> fallback ke thumbnail jika gambar asli gagal
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
- Report pengecekan disimpan ke field `report`.
- Waktu penyimpanan report disimpan ke field `report_saved_at`.
- Array embedding mentah tidak dimasukkan ke MongoDB.

Jika `check_id` yang sama digunakan lagi, sistem menolak dengan `409 Conflict`.

### 4. Report Hasil Pengecekan

Report disimpan otomatis saat registrasi metadata berhasil. Report berisi:

- `check_id`
- status registrasi
- kandidat internal dan eksternal
- skor `clip_score`, `cnn_score`, dan `final_score`
- keputusan sistem
- alasan keputusan
- status review manual jika ada

Report dapat dibaca melalui:

```text
GET /api/v1/metadata/{metadata_id}/report
```

Report ini dipakai frontend untuk fitur "Lihat Report" pada detail metadata.

## Validasi Upload

Frontend dan backend membatasi upload:

- Format: JPG, PNG, WEBP.
- Ukuran maksimal: 10 MB.
- Backend memvalidasi isi gambar dengan Pillow.
- Total piksel maksimal: 40 juta piksel.

Validasi frontend hanya untuk pengalaman user. Validasi utama tetap berada di backend.

Preprocessing gambar:

- Gambar dibaca dari bytes asli, bukan dari thumbnail frontend.
- Orientasi EXIF dinormalisasi.
- Gambar dikonversi ke RGB.
- CLIP dan CNN memakai letterbox/padding agar komposisi gambar tidak terpotong.
- Thumbnail hanya dipakai untuk tampilan UI, bukan sebagai sumber embedding gambar upload.

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

Contoh rebuild setelah perubahan preprocessing atau web search:

```powershell
docker compose up -d --build feature-extraction-service web-search-service
```

Contoh rebuild setelah perubahan orchestrator upload:

```powershell
docker compose up -d --build upload-service
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

Catatan Docker Desktop:

- Docker image dan build cache dapat memakan banyak ruang disk.
- Jika build macet atau Docker mengembalikan error `500`, cek ruang disk Docker.
- Jangan gunakan `docker compose down -v` kecuali memang ingin menghapus data MongoDB/Milvus.
- Jika memungkinkan, simpan Docker disk image di drive yang memiliki ruang besar.

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
| GET | `/api/v1/metadata/{metadata_id}/report` | Ambil report pengecekan metadata |

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
feature-extraction-service\venv\Scripts\python.exe .\scripts\evaluate_similarity.py --pairs .\evaluation_dataset\pairs.csv --output .\reports\similarity_evaluation.csv
```

Atau jika virtual environment sudah aktif:

```powershell
python .\scripts\evaluate_similarity.py --pairs .\evaluation_dataset\pairs.csv --output .\reports\similarity_evaluation.csv
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

Parameter default evaluasi:

| Parameter | Nilai |
|---|---:|
| CLIP weight | `0.4` |
| CNN weight | `0.6` |
| CLIP threshold | `0.88` |
| CNN threshold | `0.75` |
| Final threshold | `0.82` |

Catatan evaluasi:

- Jalankan ulang evaluasi setelah mengubah preprocessing gambar.
- Jika preprocessing berubah, embedding lama di Milvus perlu dibuat ulang agar konsisten.
- Jangan menyimpulkan kualitas sistem dari satu gambar saja; gunakan seluruh dataset evaluasi.

## Catatan Keamanan

- Frontend hanya mengakses API Gateway.
- Service internal dilindungi header `X-Internal-API-Key`.
- Direct access ke service internal sebaiknya tidak dibuka ke publik.
- CORS API Gateway harus dibatasi ke domain frontend.
- Secret disimpan di `.env`, bukan `settings.yaml`.
- Untuk user internal, role user belum wajib, tetapi endpoint mutasi tetap lewat gateway.
- `.env` tidak boleh di-commit.
- Jika key pernah terlanjur tersebar, lakukan rotate key.

## Troubleshooting Singkat

### Docker build gagal atau macet

1. Cek Docker Engine:

```powershell
docker info
```

2. Cek ruang disk.

3. Bersihkan build cache jika Docker sehat:

```powershell
docker builder prune -a
```

Jangan tambahkan `--volumes` jika tidak ingin menghapus data.

### Skor similarity eksternal lebih rendah dari ekspektasi

Kemungkinan penyebab:

- kandidat internet masih memakai thumbnail karena gambar asli gagal diunduh;
- gambar sumber berbeda resolusi, crop, atau kompresi;
- komposisi gambar berubah;
- hasil web search menemukan gambar yang mirip tetapi bukan file identik.

Yang dapat dicek:

- `clip_score`
- `cnn_score`
- `final_score`
- `image_url` kandidat eksternal
- apakah `image_url` masih `encrypted-tbn...` atau sudah URL gambar asli.

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

