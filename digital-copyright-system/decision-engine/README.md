# Decision Engine - Panduan Memahami Kode

Decision engine bertugas mengubah skor kemiripan menjadi keputusan sistem. Service ini tidak menghitung similarity, tetapi menilai hasil similarity berdasarkan threshold dan rule.

## Tanggung Jawab Utama

- Menerima `overall_score`, `clip_score`, dan `cnn_score`.
- Membaca preset threshold seperti `strict`, `balanced`, atau `sensitive`.
- Mendukung threshold custom dari user.
- Menentukan status kemiripan.
- Menentukan apakah hasil perlu review manual.
- Mengembalikan alasan keputusan.

## File Penting

### `app.py`

Entry point FastAPI decision engine.

Logika utamanya:
- Membuat instance FastAPI.
- Mendaftarkan router decision.
- Mengaktifkan konfigurasi middleware.

### `routers/decision_router.py`

Berisi endpoint decision.

Alur umumnya:
1. Menerima skor dari upload service.
2. Validasi request menggunakan schema.
3. Memanggil `decision_service`.
4. Mengembalikan keputusan.

Alasannya:
- Router hanya menangani HTTP.
- Logic keputusan diletakkan di service agar mudah diuji dan disesuaikan.

### `schemas/decision_schema.py`

Berisi schema request dan response.

Data penting:
- `overall_score`,
- `clip_score`,
- `cnn_score`,
- preset threshold,
- custom threshold jika ada.

Alasannya:
- Struktur input decision harus jelas karena keputusan sistem sangat bergantung pada skor.
- Pydantic membantu validasi nilai agar tidak keluar dari batas wajar.

### `services/decision_service.py`

Berisi logic utama pengambilan keputusan.

Konsep penting:
- `presets` menentukan batas high, medium, dan low berdasarkan final score.
- `score_rules` memberi sinyal tambahan dari CLIP/CNN/final score.
- `possible_similarity` digunakan untuk kondisi yang belum cukup kuat menjadi medium/high, tetapi masih layak ditinjau.
- Custom threshold dapat dipakai jika user ingin batas yang berbeda dari preset.

Contoh interpretasi mode balanced:
- score >= high berarti high similarity,
- score >= medium berarti medium similarity,
- score >= low berarti low similarity,
- score di bawah low berarti very low atau no significant similarity.

Alasannya:
- Final score saja tidak selalu cukup.
- Kadang CLIP tinggi tetapi CNN sedang, atau sebaliknya.
- Rule tambahan membantu menangkap kasus yang perlu review manual.

### `config/settings.yaml`

Menyimpan konfigurasi threshold.

Bagian penting:
- `default_preset`,
- `presets`,
- `score_rules`,
- batas minimum dan maksimum custom threshold.

Alasannya:
- Threshold perlu mudah diubah tanpa mengedit logic Python.
- Evaluasi model dapat menghasilkan threshold baru, lalu cukup disesuaikan di config.

## Hubungan Dengan Registrasi

Decision engine hanya mengembalikan keputusan. Status akhir registrasi ditentukan oleh upload service.

Contoh:
- `high_similarity`: registrasi diblokir.
- `medium_similarity` atau `possible_similarity`: perlu review manual.
- `low_similarity` atau `no_significant_similarity`: bisa lanjut registrasi.

## Catatan Desain

Decision engine dipisahkan dari similarity service agar:

- perhitungan skor dan kebijakan keputusan tidak tercampur,
- threshold bisa disesuaikan tanpa mengubah kode similarity,
- frontend dapat menampilkan alasan keputusan yang lebih jelas.
