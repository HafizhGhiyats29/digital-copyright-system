# Feature Extraction Service - Panduan Memahami Kode

Service ini bertugas mengubah gambar menjadi embedding. Embedding adalah representasi numerik dari gambar yang nantinya digunakan untuk menghitung kemiripan.

## Tanggung Jawab Utama

- Menerima gambar dari upload service atau web search service.
- Melakukan preprocessing gambar.
- Menghasilkan embedding CLIP.
- Menghasilkan embedding CNN.
- Mengembalikan embedding dalam format JSON.

## File Penting

### `app.py`

Entry point FastAPI untuk feature extraction service.

Logika utamanya:
- Membuat instance FastAPI.
- Mendaftarkan router feature extraction.
- Mengaktifkan middleware dan konfigurasi dasar.

### `routers/feature_router.py`

Berisi endpoint untuk ekstraksi fitur gambar.

Alur umumnya:
1. Menerima file gambar.
2. Membaca file sebagai image.
3. Memanggil `feature_service`.
4. Mengembalikan embedding CLIP dan CNN.

Alasannya:
- Router hanya mengatur input dan output HTTP.
- Logika ML dipindahkan ke service agar lebih rapi.

### `services/feature_service.py`

Menggabungkan hasil dari CLIP dan CNN.

Logika utamanya:
- Memanggil `clip_service` untuk embedding semantik.
- Memanggil `cnn_service` untuk embedding visual.
- Mengembalikan kedua embedding dalam satu response.

Alasannya:
- Sistem menggunakan dua jenis representasi gambar.
- CLIP kuat untuk konteks visual/semantik.
- CNN kuat untuk pola visual, bentuk, warna, dan detail gambar.

### `services/clip_service.py`

Menghasilkan embedding CLIP.

Fungsi CLIP:
- menangkap makna visual secara lebih semantik,
- membantu mengenali gambar yang mirip secara konsep,
- berguna ketika gambar tidak identik tetapi masih mirip secara konteks.

Alasannya:
- Plagiarisme visual tidak selalu berupa copy persis.
- Kadang karya memiliki konsep, pose, atau komposisi yang mirip.

### `services/cnn_service.py`

Menghasilkan embedding CNN.

Fungsi CNN:
- menangkap pola visual yang lebih rendah seperti tekstur, warna, bentuk, dan komposisi,
- membantu mendeteksi modifikasi gambar seperti crop, resize, watermark, brightness, dan contrast.

Alasannya:
- CNN membantu memperkuat deteksi kemiripan visual yang lebih teknis.
- Digabung dengan CLIP agar keputusan tidak hanya bergantung pada satu model.

### `utils/image_utils.py`

Berisi utilitas preprocessing gambar.

Biasanya mencakup:
- membuka gambar,
- mengubah gambar ke RGB,
- resize sesuai input model,
- normalisasi pixel,
- konversi ke tensor.

Alasannya:
- Model ML butuh format input yang konsisten.
- Preprocessing yang seragam membuat hasil embedding lebih stabil.

### `schemas/feature_schema.py`

Berisi bentuk response feature extraction.

Alasannya:
- Struktur response menjadi eksplisit.
- Service lain lebih mudah membaca hasil embedding.

## Catatan Desain

Service ini dipisah karena dependency ML biasanya lebih berat dibanding service lain. Jika nanti model diganti, perubahan cukup dilakukan di service ini tanpa mengubah upload service atau decision engine.

## Penjelasan Kode Per Fungsi

### `app.py`

#### `health()`

Endpoint health check.

Fungsi:
- mengembalikan status service.

Alasannya:
- memudahkan pengecekan apakah service ML siap dipanggil.

### `routers/feature_router.py`

#### `extract_image(file: UploadFile = File(...))`

Endpoint utama ekstraksi fitur.

Alur:
1. Menerima file gambar dari request.
2. Membaca file menjadi bytes.
3. Memanggil `extract_features(image_bytes)`.
4. Mengembalikan embedding CLIP dan CNN.

Alasannya:
- router hanya menangani HTTP dan file upload;
- logic model tetap berada di service layer.

### `utils/image_utils.py`

#### `load_image_from_bytes(image_bytes)`

Mengubah bytes gambar menjadi object PIL Image.

Logika:
- membaca bytes dengan `BytesIO`;
- membuka gambar memakai PIL;
- mengubah gambar menjadi RGB.

Alasannya:
- CLIP dan CNN membutuhkan format gambar yang konsisten;
- RGB menghindari masalah gambar grayscale, palette, atau alpha channel.

### `services/feature_service.py`

#### `extract_features(image_bytes)`

Fungsi utama ekstraksi semua fitur.

Alur:
1. Ubah bytes menjadi PIL Image.
2. Ambil embedding CLIP melalui `extract_clip_embedding`.
3. Ambil embedding CNN melalui `extract_cnn_embedding`.
4. Return keduanya dalam satu dictionary.

Alasannya:
- upload service cukup memanggil satu endpoint untuk mendapatkan dua jenis embedding;
- CLIP dan CNN diproses dengan input gambar yang sama.

### `services/clip_service.py`

#### `extract_clip_embedding(image)`

Menghasilkan embedding CLIP dari gambar.

Fungsi CLIP:
- menangkap kemiripan semantik atau konteks visual;
- membantu menemukan gambar yang konsepnya mirip walaupun tidak identik.

Alasan dipakai:
- plagiarisme visual bisa berupa peniruan konsep, pose, atau komposisi.

### `services/cnn_service.py`

#### `extract_cnn_embedding(image)`

Menghasilkan embedding CNN dari gambar.

Fungsi CNN:
- menangkap detail visual seperti bentuk, warna, tekstur, dan komposisi.

Alasan dipakai:
- membantu mendeteksi copy/modifikasi gambar seperti resize, crop, watermark, brightness, dan contrast.

### `schemas/feature_schema.py`

#### `FeatureResponse`

Schema response feature extraction.

Field utama:
- `clip_embedding`;
- `cnn_embedding`;
- status proses.

Alasannya:
- service pemanggil menerima format embedding yang konsisten.

### `utils/internal_auth.py`

#### `_load_env_file(path)`

Membaca `.env` lokal ke environment.

#### `get_internal_api_key()`

Mengambil internal API key.

#### `internal_auth_headers()`

Membuat header internal auth untuk request antar-service.

#### `require_internal_api_key(...)`

Dependency FastAPI untuk menolak request tanpa API key internal yang valid.

Alasannya:
- feature extraction termasuk service internal dan tidak sebaiknya dipanggil bebas dari luar.
