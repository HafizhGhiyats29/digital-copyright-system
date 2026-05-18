# Digital Copyright System

Digital Copyright System adalah sistem microservice berbasis FastAPI untuk membantu mengecek kemiripan gambar karya sebelum metadata hak cipta didaftarkan. Sistem ini mengekstrak embedding gambar memakai CLIP dan CNN, mencari kandidat gambar dari web, membandingkan kemiripan internal dan eksternal, lalu membuat keputusan apakah karya aman didaftarkan, perlu review manual, atau harus diblokir.

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Arsitektur](#arsitektur)
- [Struktur Folder](#struktur-folder)
- [Prasyarat](#prasyarat)
- [Konfigurasi](#konfigurasi)
- [Cara Menjalankan Project](#cara-menjalankan-project)
- [Cara Menggunakan Sistem](#cara-menggunakan-sistem)
- [Endpoint Penting](#endpoint-penting)
- [Menjalankan Test](#menjalankan-test)
- [Dataset dan Evaluasi](#dataset-dan-evaluasi)
- [Troubleshooting](#troubleshooting)
- [Workflow Git](#workflow-git)

## Fitur Utama

- Upload gambar untuk pengecekan indikasi plagiarisme.
- Validasi format gambar `JPEG`, `PNG`, dan `WEBP`.
- Ekstraksi fitur gambar menggunakan:
  - CLIP embedding.
  - CNN embedding berbasis ResNet.
- Reverse image search eksternal lewat SerpAPI dan Cloudinary.
- Similarity check:
  - Internal: pencarian vector di Milvus.
  - Eksternal: cosine similarity terhadap hasil web search.
- Decision engine dengan preset threshold:
  - `strict`
  - `balanced`
  - `sensitive`
- Registrasi metadata hanya jika hasil pengecekan aman.
- Review manual untuk hasil yang berada di area abu-abu.
- Penyimpanan metadata di MongoDB.
- Penyimpanan embedding permanen di Milvus.
- API Gateway sebagai pintu masuk utama aplikasi.

## Arsitektur

```text
Client / Swagger
       |
       v
API Gateway :8080
       |
       v
Upload Service :8000
       |
       +--> Feature Extraction Service :8002
       |       - CLIP embedding
       |       - CNN embedding
       |
       +--> Web Search Service :8001
       |       - Upload sementara ke Cloudinary
       |       - Reverse image search via SerpAPI
       |       - Embedding kandidat web
       |
       +--> Similarity Check Service :8003
       |       - Similarity eksternal
       |       - Similarity internal ke Milvus :19530
       |
       +--> Decision Engine :8005
       |       - Menentukan allowed / review_required / blocked
       |
       +--> Copyright Metadata Service :8006
               - Simpan metadata ke MongoDB :27017
               - Simpan referensi vector Milvus
```

Alur utama:

```text
1. User upload gambar.
2. Upload Service memvalidasi gambar.
3. Feature Extraction Service membuat CLIP dan CNN embedding.
4. Web Search Service mencari kandidat gambar serupa dari internet.
5. Similarity Check Service menghitung kemiripan internal dan eksternal.
6. Decision Engine menentukan status risiko.
7. Upload Service mengembalikan check_id dan status registrasi.
8. Jika aman, user mendaftarkan metadata menggunakan check_id.
9. Metadata disimpan ke MongoDB dan embedding dipromosikan ke Milvus.
```

## Struktur Folder

```text
digital-copyright-system/
  api-gateway/                  API utama yang mem-proxy request ke service lain
  upload-service/               Orchestrator upload, check, review, dan registrasi
  feature-extraction-service/   Ekstraksi CLIP dan CNN embedding
  web-search-service/           Reverse image search via Cloudinary + SerpAPI
  similarity-check-service/     Similarity internal Milvus dan eksternal cosine
  decision-engine/              Penentuan status risiko berdasarkan score
  copyright-metadata-service/   CRUD metadata hak cipta
  database/
    mongodb/                    Docker Compose dan data MongoDB
    milvus/                     Docker Compose dan volume Milvus
    internal_images/            Gambar internal untuk indexing/evaluasi
  evaluation_dataset/           Dataset evaluasi similarity
  scripts/                      Script evaluasi
  reports/                      Hasil laporan evaluasi
```

## Prasyarat

Install dulu software berikut:

- Python 3.11 atau lebih baru.
- Docker Desktop.
- Git.
- PowerShell atau CMD.
- Koneksi internet saat pertama kali menjalankan model karena `transformers`, `torch`, dan model CLIP dapat melakukan download model.
- Akun/API key:
  - SerpAPI untuk reverse image search.
  - Cloudinary untuk upload gambar sementara/permanen.

Catatan untuk GPU:

- `feature-extraction-service/config/settings.yaml` memakai `device: "cuda"`.
- Jika komputer tidak memiliki CUDA/GPU NVIDIA, ubah menjadi:

```yaml
device: "cpu"
```

## Konfigurasi

Konfigurasi service berada di file `config/settings.yaml` masing-masing service.

### Port Service

| Service | Port | Swagger |
| --- | ---: | --- |
| API Gateway | 8080 | `http://localhost:8080/docs` |
| Upload Service | 8000 | `http://localhost:8000/docs` |
| Web Search Service | 8001 | `http://localhost:8001/docs` |
| Feature Extraction Service | 8002 | `http://localhost:8002/docs` |
| Similarity Check Service | 8003 | `http://localhost:8003/docs` |
| Decision Engine | 8005 | `http://localhost:8005/docs` |
| Copyright Metadata Service | 8006 | `http://localhost:8006/docs` |
| MongoDB | 27017 | - |
| Milvus | 19530 | - |
| Milvus Health | 9091 | `http://localhost:9091/healthz` |
| MinIO Console Milvus | 9001 | `http://localhost:9001` |

### Credential Eksternal

Credential Cloudinary dan SerpAPI saat ini dibaca dari:

```text
digital-copyright-system/web-search-service/config/settings.yaml
digital-copyright-system/upload-service/config/settings.yaml
```

Pastikan isi credential sesuai akun sendiri. Jangan push API key asli ke repository publik.

Contoh field yang perlu dicek:

```yaml
serpapi_key: "ISI_SERPAPI_KEY_ANDA"

cloudinary:
  cloud_name: "ISI_CLOUD_NAME"
  api_key: "ISI_API_KEY"
  api_secret: "ISI_API_SECRET"
```

### MongoDB

Metadata service membaca konfigurasi MongoDB dari:

```text
digital-copyright-system/copyright-metadata-service/config/settings.yaml
```

Default:

```yaml
mongodb:
  uri: "mongodb://localhost:27017"
```

Environment variable yang didukung:

```text
MONGODB_URI
MONGODB_DATABASE
MONGODB_COLLECTION
```

### Milvus

Similarity service membaca konfigurasi Milvus dari:

```text
digital-copyright-system/similarity-check-service/config/settings.yaml
```

Default:

```yaml
milvus_host: "localhost"
milvus_port: "19530"
milvus_collection_name: "copyright_embeddings"
```

## Cara Menjalankan Project

Masuk ke folder project utama:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system"
```

### 1. Jalankan MongoDB

Buka terminal pertama:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\database\mongodb"
docker compose up -d
```

Cek container:

```powershell
docker ps
```

MongoDB harus berjalan di port `27017`.

### 2. Jalankan Milvus

Buka terminal kedua:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\database\milvus"
docker compose up -d
```

Cek health Milvus:

```powershell
curl http://localhost:9091/healthz
```

Tunggu sampai Milvus benar-benar sehat sebelum menjalankan similarity service.

### 3. Buat Virtual Environment Tiap Service

Setiap service punya dependency sendiri. Jalankan per service:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\nama-service"
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Ulangi untuk service berikut:

```text
api-gateway
upload-service
feature-extraction-service
web-search-service
similarity-check-service
decision-engine
copyright-metadata-service
```

Jika folder `venv` sudah ada dan dependency sudah terinstall, cukup aktifkan saja:

```powershell
.\venv\Scripts\activate
```

### 4. Jalankan Semua Service

Buka terminal terpisah untuk setiap service.

#### Terminal 1 - Metadata Service

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\copyright-metadata-service"
.\venv\Scripts\activate
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8006
```

#### Terminal 2 - Feature Extraction Service

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\feature-extraction-service"
.\venv\Scripts\activate
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8002
```

#### Terminal 3 - Web Search Service

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\web-search-service"
.\venv\Scripts\activate
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

#### Terminal 4 - Similarity Check Service

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\similarity-check-service"
.\venv\Scripts\activate
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8003
```

#### Terminal 5 - Decision Engine

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\decision-engine"
.\venv\Scripts\activate
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8005
```

#### Terminal 6 - Upload Service

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\upload-service"
.\venv\Scripts\activate
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 7 - API Gateway

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\api-gateway"
.\venv\Scripts\activate
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8080
```

Setelah semua service hidup, buka:

```text
http://localhost:8080/docs
```

### 5. Cek Health Service

```powershell
curl http://localhost:8080/health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8005/health
curl http://localhost:8006/health
```

## Setup Milvus Collection

Sebelum embedding disimpan permanen, collection Milvus perlu dibuat.

Jalankan setelah Milvus dan dependency similarity service siap:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\similarity-check-service"
.\venv\Scripts\activate
python .\scripts\create_milvus_collection.py
```

Jika ingin memasukkan gambar internal dari `database/internal_images`:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\similarity-check-service"
.\venv\Scripts\activate
python .\scripts\insert_internal_images.py
```

Pastikan `feature-extraction-service` sudah berjalan di port `8002` sebelum menjalankan script insert internal images.

## Cara Menggunakan Sistem

Gunakan API Gateway sebagai pintu masuk utama:

```text
http://localhost:8080/docs
```

### 1. Upload Gambar Untuk Dicek

Endpoint:

```text
POST /api/v1/upload
```

Di Swagger:

1. Buka `http://localhost:8080/docs`.
2. Pilih endpoint `POST /api/v1/upload`.
3. Klik `Try it out`.
4. Upload file gambar pada field `file`.
5. Isi `preset` jika perlu:
   - `strict`
   - `balanced`
   - `sensitive`
6. Klik `Execute`.

Response penting:

```json
{
  "status": "processed",
  "check_id": "uuid-hasil-cek",
  "can_register": true,
  "registration_status": "allowed",
  "registration_reason": "Registrasi diizinkan karena tidak ada indikasi plagiarisme yang perlu ditinjau."
}
```

Arti `registration_status`:

| Status | Arti |
| --- | --- |
| `allowed` | Gambar aman untuk didaftarkan. |
| `review_required` | Gambar belum boleh didaftarkan sebelum reviewer approve. |
| `blocked` | Gambar ditolak karena kemiripan tinggi. |

### 2. Registrasi Metadata Setelah Aman

Jika `can_register = true`, lanjutkan ke:

```text
POST /api/v1/register-metadata
```

Contoh body:

```json
{
  "check_id": "uuid-hasil-cek",
  "ki_id": "4686",
  "ki_uuid": "HCNA1506232226",
  "title": "Judul Karya",
  "description": "Deskripsi karya",
  "category": "HAK CIPTA",
  "sub_category": "Karya Seni",
  "copyright_category": "Karya Seni",
  "copyright_sub_category": "Seni Ilustrasi",
  "image_url": null,
  "cloudinary_public_id": null
}
```

Saat registrasi berhasil:

- Metadata dibuat di MongoDB.
- Gambar disimpan ke Cloudinary jika `image_url` belum diberikan.
- Embedding sementara dari proses upload disimpan permanen ke Milvus.
- Metadata diupdate dengan referensi `milvus_collection`, `milvus_id`, `embedding_version`, dan `embedding_status`.

### 3. Review Manual

Jika hasil upload mengembalikan `review_required`, reviewer dapat memilih:

```text
POST /api/v1/review-check/{check_id}/approve
POST /api/v1/review-check/{check_id}/reject
```

Contoh body approve:

```json
{
  "reason": "Kemiripan hanya pada konsep umum, bukan visual yang sama."
}
```

Setelah `approve`, gunakan `check_id` yang sama untuk `POST /api/v1/register-metadata`.

### 4. Melihat Metadata

Endpoint:

```text
GET /api/v1/metadata
GET /api/v1/metadata/{metadata_id}
```

### 5. Menghapus Metadata

Endpoint:

```text
DELETE /api/v1/metadata/{metadata_id}
```

Gateway akan mencoba membersihkan:

- Gambar di Cloudinary jika ada `cloudinary_public_id`.
- Vector di Milvus.
- Metadata di MongoDB.

## Endpoint Penting

### API Gateway

Base URL:

```text
http://localhost:8080
```

| Method | Endpoint | Fungsi |
| --- | --- | --- |
| GET | `/health` | Health check gateway |
| POST | `/api/v1/upload` | Upload dan cek plagiarisme |
| POST | `/api/v1/register-metadata` | Registrasi metadata setelah pengecekan aman |
| POST | `/api/v1/review-check/{check_id}/approve` | Approve hasil review manual |
| POST | `/api/v1/review-check/{check_id}/reject` | Reject hasil review manual |
| GET | `/api/v1/metadata` | List metadata |
| POST | `/api/v1/metadata` | Create metadata langsung |
| GET | `/api/v1/metadata/{metadata_id}` | Detail metadata |
| PUT | `/api/v1/metadata/{metadata_id}` | Update metadata |
| PATCH | `/api/v1/metadata/{metadata_id}/embedding` | Update referensi embedding |
| DELETE | `/api/v1/metadata/{metadata_id}` | Hapus metadata + vector + gambar |
| DELETE | `/api/v1/metadata/{metadata_id}/vector` | Hapus vector Milvus saja |

### Upload Service

Base URL:

```text
http://localhost:8000
```

| Method | Endpoint | Fungsi |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/upload` | Orkestrasi pengecekan gambar |
| POST | `/register-metadata` | Registrasi metadata menggunakan `check_id` |
| POST | `/review-check/{check_id}/approve` | Approve review |
| POST | `/review-check/{check_id}/reject` | Reject review |
| POST | `/cloudinary/delete` | Hapus gambar Cloudinary |

### Feature Extraction Service

Base URL:

```text
http://localhost:8002
```

| Method | Endpoint | Fungsi |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/extract` | Ekstraksi CLIP dan CNN embedding dari gambar |

### Web Search Service

Base URL:

```text
http://localhost:8001
```

| Method | Endpoint | Fungsi |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/search` | Reverse image search dan embedding kandidat |

### Similarity Check Service

Base URL:

```text
http://localhost:8003
```

| Method | Endpoint | Fungsi |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/similarity` | Hitung kemiripan internal dan eksternal |
| POST | `/embeddings` | Simpan embedding ke Milvus |
| DELETE | `/embeddings/{metadata_id}` | Hapus embedding berdasarkan metadata ID |

### Decision Engine

Base URL:

```text
http://localhost:8005
```

| Method | Endpoint | Fungsi |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/decision` | Buat keputusan risiko dari similarity score |

### Copyright Metadata Service

Base URL:

```text
http://localhost:8006
```

| Method | Endpoint | Fungsi |
| --- | --- | --- |
| GET | `/health` | Health check |
| GET | `/` | Info service |
| POST | `/metadata/migrate-json-to-mongodb` | Migrasi data JSON lokal ke MongoDB |
| POST | `/metadata` | Create metadata |
| GET | `/metadata` | List metadata |
| GET | `/metadata/{metadata_id}` | Detail metadata |
| PUT | `/metadata/{metadata_id}` | Update metadata |
| PATCH | `/metadata/{metadata_id}/embedding` | Update referensi embedding |
| DELETE | `/metadata/{metadata_id}` | Delete metadata |

## Preset Decision Engine

Konfigurasi berada di:

```text
digital-copyright-system/decision-engine/config/settings.yaml
```

Default:

| Preset | High | Medium | Low |
| --- | ---: | ---: | ---: |
| `strict` | 0.90 | 0.75 | 0.60 |
| `balanced` | 0.85 | 0.70 | 0.55 |
| `sensitive` | 0.80 | 0.65 | 0.50 |

Aturan registrasi secara umum:

```text
high_similarity      -> blocked
possible_plagiarism  -> review_required
medium_similarity    -> review_required
low_similarity       -> allowed
no_significant       -> allowed
```

Custom threshold juga bisa dikirim saat upload:

```text
high_threshold
medium_threshold
low_threshold
```

Jika memakai custom threshold, ketiganya wajib diisi.

## Menjalankan Test

Jalankan test per service dari folder service masing-masing.

Contoh API Gateway:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\api-gateway"
.\venv\Scripts\activate
python -m pytest -q
```

Contoh Metadata Service:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\copyright-metadata-service"
.\venv\Scripts\activate
python -m pytest -q
```

Contoh Upload Service:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system\upload-service"
.\venv\Scripts\activate
python -m pytest -q
```

Service yang memiliki folder `tests`:

```text
api-gateway
copyright-metadata-service
feature-extraction-service
similarity-check-service
upload-service
web-search-service
```

## Dataset dan Evaluasi

Dataset evaluasi ada di:

```text
digital-copyright-system/evaluation_dataset
```

Kategori dataset:

```text
same
modified
semantic_similar
different
```

Script evaluasi:

```text
digital-copyright-system/scripts/evaluate_similarity.py
```

Contoh menjalankan evaluasi:

```powershell
cd "E:\Hafizh Code\Capstone2\digital-copyright-system"
python .\scripts\evaluate_similarity.py --output .\reports\similarity_evaluation.csv
```

Hasil laporan tersimpan di folder:

```text
digital-copyright-system/reports
```

## Troubleshooting

### 1. `ModuleNotFoundError`

Pastikan virtual environment service aktif dan dependency sudah diinstall:

```powershell
.\venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 2. Feature extraction gagal karena CUDA

Jika tidak punya GPU CUDA, ubah:

```yaml
device: "cuda"
```

menjadi:

```yaml
device: "cpu"
```

di:

```text
feature-extraction-service/config/settings.yaml
```

### 3. Milvus belum siap

Cek container:

```powershell
docker ps
```

Cek health:

```powershell
curl http://localhost:9091/healthz
```

Jika belum sehat, tunggu beberapa saat lalu ulangi.

### 4. Similarity service gagal connect Milvus

Pastikan:

- Milvus berjalan di port `19530`.
- Collection sudah dibuat dengan `create_milvus_collection.py`.
- Konfigurasi `milvus_host` dan `milvus_port` benar.

### 5. Web search gagal

Pastikan:

- `serpapi_key` valid.
- Credential Cloudinary valid.
- Internet aktif.
- Limit API SerpAPI/Cloudinary belum habis.

### 6. Upload service gagal memanggil service lain

Pastikan semua service berjalan di port sesuai konfigurasi:

```text
feature_service_url: http://localhost:8002/extract
web_search_service_url: http://localhost:8001/search
similarity_service_url: http://localhost:8003/similarity
decision_service_url: http://localhost:8005/decision
metadata_service_url: http://localhost:8006/metadata
```

### 7. Port sudah dipakai

Cek proses yang memakai port:

```powershell
netstat -ano | findstr :8080
```

Ganti `8080` dengan port yang bermasalah.

### 8. Swagger tidak muncul

Pastikan service sudah dijalankan dengan uvicorn dan buka URL sesuai port:

```text
http://localhost:<PORT>/docs
```

## Workflow Git

Clone repository:

```powershell
git clone https://github.com/HafizhGhiyats29/digital-copyright-system.git
cd digital-copyright-system
```

Ambil update terbaru:

```powershell
git pull origin main
```

Buat branch kerja:

```powershell
git checkout -b nama-fitur
```

Cek perubahan:

```powershell
git status
```

Commit perubahan:

```powershell
git add .
git commit -m "deskripsi perubahan"
```

Push branch:

```powershell
git push -u origin nama-fitur
```

Jika bekerja langsung di branch `main`, pastikan sudah pull update terbaru sebelum push.

## Catatan Penting

- File `digital-copyright-system/docker-compose.yml` utama saat ini kosong. Untuk menjalankan database gunakan compose di `database/mongodb` dan `database/milvus`.
- Jalankan API lewat API Gateway (`http://localhost:8080/docs`) agar alur antar-service lebih mudah dipakai.
- Untuk demo lokal tanpa GPU, gunakan `device: "cpu"` pada feature extraction.
- Jangan menyimpan API key asli di repository publik.
