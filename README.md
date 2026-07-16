# Digital Copyright System

Digital Copyright System adalah sistem microservice untuk mengecek kemiripan gambar karya sebelum metadata hak cipta didaftarkan. Sistem mengekstrak embedding gambar menggunakan CLIP dan CNN, mencari kandidat kemiripan internal dan eksternal, mengambil keputusan risiko plagiarisme, lalu menyimpan metadata, gambar, report pemeriksaan, dan referensi embedding karya yang lolos verifikasi.

## Daftar Isi

- [System Requirements](#system-requirements)
- [Fitur Utama](#fitur-utama)
- [Ringkasan Perubahan Terbaru](#ringkasan-perubahan-terbaru)
- [Arsitektur](#arsitektur)
- [Struktur Folder](#struktur-folder)
- [Identitas Data](#identitas-data)
- [Alur Sistem](#alur-sistem)
- [Validasi Upload](#validasi-upload)
- [Konfigurasi](#konfigurasi)
- [Menjalankan Dengan Docker](#menjalankan-dengan-docker)
- [Menjalankan Frontend](#menjalankan-frontend)
- [Endpoint Utama](#endpoint-utama)
- [Bulk Import Dataset Artwork](#bulk-import-dataset-artwork)
- [Status Pengujian Terakhir](#status-pengujian-terakhir)
- [Catatan Performa](#catatan-performa)
- [Evaluasi Similarity](#evaluasi-similarity)
- [Catatan Keamanan](#catatan-keamanan)
- [Troubleshooting Singkat](#troubleshooting-singkat)
- [Dokumentasi Tambahan](#dokumentasi-tambahan)

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
| GPU | Aplikasi dapat berjalan di CPU, tetapi konfigurasi Docker saat ini meminta GPU NVIDIA melalui `gpus: all` |

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
- Docker Compose saat ini menyimpan cache Hugging Face dan Torch pada volume `feature-model-cache`, sehingga model tidak perlu diunduh ulang setiap container dibuat ulang.
- Untuk konfigurasi `gpus: all`, Docker Desktop harus dapat mengakses NVIDIA GPU dan driver/CUDA container runtime yang sesuai.
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

## Ringkasan Perubahan Terbaru

Perubahan implementasi dan operasional yang sudah diterapkan pada lingkungan lokal:

| Area | Perubahan |
|---|---|
| Feature extraction | Mengaktifkan GPU Docker dengan `gpus: all` untuk CLIP dan CNN. |
| Model cache | Menambahkan `HF_HOME`, `TORCH_HOME`, dan volume persisten `feature-model-cache`. |
| Ketahanan service | Menambahkan `restart: unless-stopped` pada feature extraction service. |
| Similarity runtime | Bobot aktif diatur menjadi CLIP `0.3` dan CNN `0.7`, dengan top-k internal/eksternal masing-masing `3`. |
| Decision request | Skor cosine di-clamp ke `[0, 1]` sebelum validasi decision engine untuk mencegah error `422`. |
| API Gateway | Timeout request dapat dioverride melalui `REQUEST_TIMEOUT_SECONDS` dan saat ini digunakan nilai `180`. |
| SerpAPI | Key dari `.env` diterapkan dengan recreate `web-search-service`; secret tidak ditulis ke dokumentasi. |
| Bulk import | Menambahkan workflow import dataset original melalui API lengkap dengan threshold, checkpoint, retry, dan anti-duplikasi `dataset_image_id`. |
| Checkpoint | Database/API menjadi sumber kebenaran sehingga checkpoint `registered` yang stale tidak menyebabkan data hilang dilewati. |
| Cleanup metadata | Endpoint delete gateway membersihkan Cloudinary, Milvus, dan MongoDB sebagai satu alur. |
| Evaluasi | Menambahkan command evaluasi pasangan transformasi dan output metrik per transformasi. |
| Pengujian data | Lingkungan diverifikasi dengan total 200 metadata, seluruh embedding `ready`, seluruh URL Cloudinary terisi, dan tanpa kegagalan checkpoint akhir. |

Error download model Hugging Face, resolusi nama service, dan koneksi Cloudinary yang ditemukan sebelumnya dikonfirmasi sebagai masalah jaringan/DNS. Tidak ada workaround fungsional sementara yang dipertahankan pada web search service; solusi operasionalnya adalah memperbaiki jaringan, DNS, firewall, atau proxy container.

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
REQUEST_TIMEOUT_SECONDS=180
```

Prinsip konfigurasi:

- `settings.yaml` untuk default lokal yang aman masuk Git.
- `.env` untuk secret dan override environment.
- Jangan commit `.env` berisi key asli.
- Perubahan `.env` tidak otomatis masuk ke container yang sedang berjalan. Container terkait harus dibuat ulang.

Konfigurasi runtime similarity saat ini berada di `digital-copyright-system/similarity-check-service/config/settings.yaml`:

| Parameter | Nilai |
|---|---:|
| CLIP weight | `0.3` |
| CNN weight | `0.7` |
| Internal top-k | `3` |
| External top-k | `3` |
| Milvus metric | `COSINE` |

Skor cosine dinormalisasi ke rentang `[0, 1]` sebelum dikirim ke decision engine. Normalisasi ini mencegah error `422 Unprocessable Entity` ketika hasil floating-point sedikit lebih besar dari `1.0`, misalnya `1.00000008`.

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

Terapkan ulang perubahan `.env` tanpa rebuild image:

```powershell
docker compose up -d --force-recreate
```

Jika hanya `SERPAPI_KEY` atau konfigurasi web search yang berubah:

```powershell
docker compose up -d --force-recreate --no-deps web-search-service
```

Jika hanya bobot similarity berubah:

```powershell
docker compose up -d --build --no-deps similarity-check-service
```

Jika timeout gateway berubah:

```powershell
docker compose up -d --force-recreate --no-deps api-gateway
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

Konfigurasi khusus feature extraction pada Docker Compose:

- `gpus: all` mengaktifkan GPU untuk CLIP dan CNN.
- `HF_HOME=/root/.cache/huggingface` menyimpan cache model Hugging Face.
- `TORCH_HOME=/root/.cache/torch` menyimpan cache model Torch.
- Volume `feature-model-cache:/root/.cache` mempertahankan model setelah container di-recreate.
- `restart: unless-stopped` membuat feature service kembali aktif setelah Docker restart.

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

Penghapusan metadata melalui gateway diorkestrasi sebagai satu alur. Gateway mengambil referensi metadata terlebih dahulu, lalu menghapus gambar Cloudinary, vector Milvus, dan dokumen MongoDB. Jangan menghapus dokumen MongoDB secara langsung jika resource Cloudinary dan Milvus juga harus dibersihkan.

## Bulk Import Dataset Artwork

Script bulk import tersedia di:

```text
digital-copyright-system/scripts/bulk_register_artworks.py
```

Script ini memasukkan gambar original dari `evaluation_dataset/artworks_met` melalui alur aplikasi yang sama dengan upload manual:

```text
gambar original
  -> POST /api/v1/upload
  -> ekstraksi CLIP dan CNN
  -> web search SerpAPI
  -> similarity internal dan eksternal
  -> decision engine
  -> approval dataset pengujian jika diperlukan
  -> upload permanen Cloudinary
  -> metadata MongoDB
  -> embedding Milvus
```

Jalankan dari folder `digital-copyright-system`:

```powershell
.\feature-extraction-service\venv\Scripts\python.exe scripts\bulk_register_artworks.py --limit 199 --high-threshold 0.98 --medium-threshold 0.97 --low-threshold 0.96 --approve-review --request-timeout 240
```

Arti parameter penting:

| Parameter | Fungsi |
|---|---|
| `--limit` | Jumlah baris dataset yang dipertimbangkan dari posisi `--start` |
| `--start` | Posisi awal dataset, default `0` |
| `--high-threshold` | Batas high similarity, default `0.98` |
| `--medium-threshold` | Batas medium similarity, default `0.97` |
| `--low-threshold` | Batas low similarity, default `0.96` |
| `--approve-review` | Approve otomatis hasil review/blocked khusus dataset CC0/Public Domain untuk pengujian |
| `--request-timeout` | Timeout client bulk import dalam detik |

Ketentuan bulk import:

- Gunakan `--approve-review` hanya untuk dataset pengujian yang lisensinya sudah diketahui, bukan untuk upload pengguna umum.
- Setiap metadata dataset diberi penanda `dataset_image_id=<image_id>` pada deskripsi.
- API/database menjadi sumber kebenaran. Checkpoint CSV lama tidak menyebabkan data yang sudah terhapus dari database dilewati.
- Script aman dijalankan ulang: data yang masih ada di API dilewati berdasarkan `dataset_image_id`, sedangkan checkpoint yang sudah stale akan dicoba ulang.
- Progres dan error disimpan setelah setiap gambar ke `reports/bulk_artwork_registration.csv`.
- Jika targetnya 200 metadata total dan database sudah memiliki satu metadata non-dataset, gunakan `--limit 199`. Jika database benar-benar kosong dan seluruh 200 artwork ingin dimasukkan, gunakan `--limit 200`.
- Setiap gambar dapat memakai satu pencarian SerpAPI. Pastikan kuota key mencukupi sebelum memulai import besar.

## Status Pengujian Terakhir

Verifikasi bulk import terakhir dilakukan pada 13 Juli 2026 melalui API Gateway dan menghasilkan:

| Pemeriksaan | Hasil |
|---|---:|
| Total metadata | `200` |
| Artwork original dari dataset | `199` |
| Metadata awal non-dataset | `1` |
| `dataset_image_id` unik | `199` |
| Embedding berstatus `ready` | `200` |
| Metadata dengan URL Cloudinary | `200` |
| URL gambar kosong | `0` |
| Gagal pada checkpoint akhir | `0` |
| Frontend `http://localhost:4173/` | HTTP `200` |

Hasil ini adalah snapshot lingkungan lokal pengujian, bukan fixture yang dijamin selalu sama. Jumlah dapat berubah setelah operasi tambah atau hapus metadata.

## Catatan Performa

Jumlah vector 100 atau 200 bukan penyebab utama perubahan waktu upload pada pengujian saat ini. Similarity internal hanya mengambil top-3 dari Milvus dan umumnya selesai jauh di bawah satu detik.

Contoh pengukuran satu request yang membutuhkan sekitar 25 detik:

| Tahap | Perkiraan waktu |
|---|---:|
| Ekstraksi embedding gambar asli | `0.12` detik |
| Web search, termasuk Cloudinary, SerpAPI, dan kandidat | `24.88` detik |
| Similarity Milvus dan enrichment metadata | `0.05` detik |
| Decision engine | `0.01` detik |

Kesimpulan performa:

- Latensi paling besar dan paling berubah-ubah berasal dari jaringan eksternal, terutama Google Lens melalui SerpAPI.
- Web search juga mengunduh maksimal tiga kandidat dan membuat embedding kandidat secara paralel.
- Gambar asli dari kandidat dicoba lebih dulu; thumbnail dipakai sebagai fallback.
- Respons SerpAPI dapat selesai cepat pada satu request dan membutuhkan lebih dari 20 detik pada request lain.
- `REQUEST_TIMEOUT_SECONDS=180` dipakai agar API Gateway tidak memotong request web search yang valid pada detik ke-60.
- Bandingkan performa memakai beberapa request dan catat waktu per tahap; jangan menyimpulkan skalabilitas Milvus hanya dari total waktu endpoint upload.

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

Evaluasi pasangan transformasi dapat dijalankan dalam satu baris:

```powershell
.\feature-extraction-service\venv\Scripts\python.exe scripts\evaluate_similarity.py --pairs evaluation_dataset\pairs_transformations.csv --output reports\similarity_evaluation_transformations.csv --metrics-output reports\similarity_metrics_by_transformation.csv
```

Output evaluasi transformasi:

```text
digital-copyright-system/reports/similarity_evaluation_transformations.csv
digital-copyright-system/reports/similarity_metrics_by_transformation.csv
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

Bobot pada tabel evaluasi berasal dari default script evaluasi dan dapat berbeda dari bobot runtime service (`CLIP 0.3`, `CNN 0.7`). Saat membandingkan laporan evaluasi dengan perilaku website, pastikan kedua konfigurasi menggunakan bobot yang sama.

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

### Docker gagal mengunduh model Hugging Face

Gejala umum:

```text
OSError: Can't load the configuration of 'openai/clip-vit-base-patch32'
```

Yang perlu diperiksa:

1. Pastikan container memiliki koneksi internet dan DNS dapat menyelesaikan `huggingface.co`.
2. Pastikan tidak ada firewall, proxy, atau jaringan kampus/kantor yang memblokir Hugging Face.
3. Coba jaringan lain jika koneksi ditolak atau DNS gagal.
4. Setelah model berhasil diunduh, volume `feature-model-cache` akan menyimpan cache untuk startup berikutnya.

### Cloudinary connection refused

Gejala umum:

```text
MaxRetryError
Failed to establish a new connection
Connection refused
```

Error ini umumnya berasal dari jaringan container menuju `api.cloudinary.com`, bukan dari algoritma web search. Periksa koneksi, DNS Docker, firewall, proxy, dan coba jaringan lain sebelum mengubah implementasi service.

### Service Docker tidak menemukan service lain

Gejala umum:

```text
httpx.ConnectError: [Errno -2] Name or service not known
```

Pastikan:

- semua container berada pada network `digital-copyright-network`;
- URL antar-container memakai nama service Compose, misalnya `http://feature-extraction-service:8002`;
- browser/host memakai `localhost`, bukan nama service Docker;
- container tujuan berstatus `Up` dan sudah menyelesaikan startup.

### Perubahan `.env` belum digunakan container

Periksa nilai aktif tanpa menampilkan secret, lalu recreate service yang memakai variabel tersebut. Untuk SerpAPI:

```powershell
docker compose up -d --force-recreate --no-deps web-search-service
```

`SERPAPI_KEY` dibaca saat module web search di-import, sehingga restart/recreate diperlukan. Jangan menampilkan key asli pada README, terminal bersama, screenshot, atau log aplikasi.

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

