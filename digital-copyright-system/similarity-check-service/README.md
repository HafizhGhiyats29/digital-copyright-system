# Similarity Check Service - Panduan Memahami Kode

Service ini bertugas membandingkan embedding gambar baru dengan kandidat internal dan eksternal. Hasil akhirnya berupa skor kemiripan, daftar kandidat teratas, dan kandidat terbaik.

## Tanggung Jawab Utama

- Menghitung cosine similarity antara embedding query dan kandidat.
- Menggabungkan skor CLIP dan CNN menjadi final score.
- Mencari kandidat internal dari Milvus.
- Membandingkan kandidat eksternal dari web search.
- Mengambil metadata internal dari copyright-metadata-service.
- Menyimpan, mencari, dan menghapus vector di Milvus.

## File Penting

### `app.py`

Entry point FastAPI similarity-check service.

Logika utamanya:
- Membuat aplikasi FastAPI.
- Mendaftarkan router similarity.
- Menyiapkan konfigurasi service.

### `routers/similarity_route.py`

Berisi endpoint untuk:
- similarity check,
- insert embedding ke Milvus,
- delete embedding dari Milvus,
- health check terkait vector storage.

Alasannya:
- Service lain tidak perlu berkomunikasi langsung dengan Milvus.
- Semua operasi vector storage dikendalikan dari satu service.

### `services/cosine_service.py`

Berisi logika perhitungan cosine similarity.

Konsep utamanya:
- cosine similarity mengukur arah dua vector,
- nilai mendekati 1 berarti sangat mirip,
- nilai mendekati 0 berarti tidak mirip.

Final score dibuat dari gabungan:
- `clip_score` untuk konteks visual,
- `cnn_score` untuk detail visual.

Alasannya:
- CLIP dan CNN memiliki kekuatan berbeda.
- Gabungan skor membuat hasil lebih seimbang dibanding hanya memakai satu model.

### `services/milvus_client.py`

Berisi komunikasi dengan Milvus.

Tugasnya:
- koneksi ke Milvus,
- memastikan collection tersedia,
- insert embedding,
- search embedding,
- delete embedding berdasarkan `metadata_id`,
- mengembalikan hasil pencarian internal.

Alasannya:
- Milvus dipakai karena pencarian vector akan semakin berat jika data gambar bertambah.
- Database biasa seperti MongoDB tidak ideal untuk nearest neighbor search.

### `services/similarity_service.py`

Mengatur proses similarity secara keseluruhan.

Alur umumnya:
1. Terima embedding query dari upload service.
2. Cari kandidat internal dari Milvus.
3. Hitung kandidat eksternal dari hasil web search.
4. Gabungkan internal dan eksternal.
5. Urutkan berdasarkan final score.
6. Ambil kandidat terbaik.
7. Enrich kandidat internal dengan metadata.
8. Kembalikan top 3 internal, top 3 external, dan top 3 combined.

Alasannya:
- User perlu tahu sumber kemiripan: internal atau eksternal.
- Metadata internal membuat hasil lebih mudah dibaca di frontend.

### `services/metadata_client.py`

Mengambil detail metadata berdasarkan `metadata_id`.

Alasannya:
- Milvus hanya menyimpan referensi vector.
- Informasi seperti judul, kategori, dan image URL tetap berada di metadata service.

### `scripts/create_milvus_collection.py`

Script untuk membuat collection Milvus.

Collection menyimpan:
- `metadata_id`,
- `embedding_version`,
- `clip_embedding`,
- `cnn_embedding`.

Alasannya:
- Satu karya punya satu row vector yang berisi dua embedding.
- `metadata_id` menjadi penghubung antara Milvus dan MongoDB.

### `scripts/insert_internal_images.py`

Script untuk memasukkan dataset internal awal ke Milvus.

Alasannya:
- Sistem butuh database pembanding internal.
- Dataset internal bisa digunakan untuk simulasi dan evaluasi.

## Catatan Desain

Milvus hanya menyimpan vector dan referensi. Metadata lengkap tetap berada di MongoDB. Pola ini membuat sistem lebih rapi:

- MongoDB untuk data deskriptif.
- Milvus untuk pencarian kemiripan vector.
- Cloudinary untuk file gambar.
