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

## Penjelasan Kode Per Fungsi

### `app.py`

#### `health()`

Endpoint health check similarity service.

Alasannya:
- memastikan service pencarian similarity siap dipanggil.

### `routers/similarity_route.py`

#### `similarity_check(request: SimilarityRequest)`

Endpoint utama similarity check.

Alur:
1. Terima embedding query CLIP dan CNN.
2. Terima kandidat eksternal dari web search.
3. Panggil `compute_similarity`.
4. Return hasil top internal, top external, dan combined.

Alasannya:
- upload service tidak perlu tahu detail perhitungan similarity.

#### `create_embedding(request: EmbeddingInsertRequest)`

Endpoint untuk menyimpan embedding baru ke Milvus.

Dipakai saat:
- metadata berhasil dibuat;
- embedding sementara dipromosikan menjadi data internal.

#### `delete_embedding(metadata_id: str)`

Endpoint untuk menghapus vector Milvus berdasarkan metadata ID.

Alasannya:
- saat metadata dihapus, vector internalnya juga harus dibersihkan.

### `services/cosine_service.py`

#### `cosine_similarity(vec1, vec2)`

Menghitung cosine similarity dua vector.

Rumus konsep:

```text
cosine = dot(vec1, vec2) / (norm(vec1) * norm(vec2))
```

Makna:
- mendekati 1 berarti sangat mirip;
- mendekati 0 berarti tidak mirip.

Alasannya:
- embedding gambar lebih cocok dibandingkan berdasarkan arah vector daripada jarak mentah.

#### `compute_external_similarity(query_clip_embedding, query_cnn_embedding, matches)`

Menghitung similarity terhadap kandidat eksternal dari web search.

Alur:
1. Loop setiap kandidat web.
2. Hitung `clip_score`.
3. Hitung `cnn_score`.
4. Gabungkan menjadi `final_score`.
5. Simpan data kandidat dan skor.

Alasannya:
- kandidat eksternal tidak berada di Milvus;
- karena jumlahnya sedikit, cukup dihitung langsung dengan cosine similarity.

### `services/milvus_client.py`

#### `get_collection()`

Membuka collection Milvus yang dipakai sistem.

Alasannya:
- semua operasi insert/search/delete membutuhkan object collection.

#### `validate_embedding_dimensions(clip_embedding, cnn_embedding)`

Memastikan dimensi embedding sesuai schema collection.

Alasannya:
- Milvus akan error jika dimensi vector tidak sesuai;
- validasi lebih awal membuat error lebih mudah dipahami.

#### `insert_embedding(metadata_id, clip_embedding, cnn_embedding, embedding_version)`

Menyimpan embedding ke Milvus.

Data yang disimpan:
- `metadata_id`;
- `embedding_version`;
- `clip_embedding`;
- `cnn_embedding`.

Alasannya:
- satu karya disimpan sebagai satu row yang punya dua vector.
- `metadata_id` menjadi penghubung ke MongoDB.

#### `search_single_vector(collection, query_embedding, vector_field, top_k)`

Mencari kandidat internal berdasarkan satu field vector.

Contoh:
- search pada `clip_embedding`;
- search pada `cnn_embedding`.

Alasannya:
- Milvus melakukan vector search per field;
- hasil CLIP dan CNN kemudian digabung.

#### `merge_internal_results(clip_results, cnn_results)`

Menggabungkan hasil search CLIP dan CNN.

Alur:
1. Gabungkan kandidat berdasarkan `metadata_id`.
2. Ambil score CLIP jika ada.
3. Ambil score CNN jika ada.
4. Hitung `final_score`.
5. Urutkan kandidat.

Alasannya:
- satu kandidat bisa muncul dari CLIP, CNN, atau keduanya.
- sistem butuh satu skor final per kandidat.

#### `search_internal_similarity(query_clip_embedding, query_cnn_embedding, top_k=3)`

Fungsi utama pencarian internal di Milvus.

Alur:
1. Search dengan CLIP.
2. Search dengan CNN.
3. Merge hasil.
4. Return top kandidat internal.

Alasannya:
- database internal bisa besar;
- Milvus mempercepat pencarian kandidat terdekat.

#### `_escape_milvus_string(value: str)`

Membersihkan string sebelum dipakai dalam expression Milvus.

Alasannya:
- mencegah error query ketika string mengandung karakter khusus.

#### `delete_embedding_by_metadata_id(metadata_id: str)`

Menghapus vector berdasarkan metadata ID.

Alasannya:
- metadata dan vector harus tetap sinkron.

### `services/similarity_service.py`

#### `sort_by_score(results)`

Mengurutkan hasil berdasarkan `final_score` tertinggi.

#### `get_top_results(results, limit)`

Mengambil top-N hasil setelah sorting.

#### `get_best_score(results)`

Mengambil skor terbaik dari daftar hasil.

Dipakai untuk:
- `best_internal_score`;
- `best_external_score`.

#### `build_final_response(internal_results, external_results)`

Membangun response final untuk frontend.

Isi response:
- `overall_score`;
- `best_source`;
- `best_match`;
- summary;
- top 3 internal;
- top 3 external;
- top 3 combined.

Alasannya:
- frontend perlu melihat hasil internal dan eksternal secara terpisah;
- decision engine hanya butuh skor terbaik.

#### `compute_similarity(query_clip_embedding, query_cnn_embedding, web_matches)`

Fungsi utama similarity service.

Alur:
1. Cari kandidat internal di Milvus.
2. Enrich kandidat internal dengan metadata.
3. Hitung kandidat eksternal dari web search.
4. Gabungkan hasil.
5. Bangun response akhir.

Alasannya:
- internal dan eksternal punya sumber berbeda;
- hasil akhir perlu disatukan agar decision engine bisa membaca skor terbaik.

### `services/metadata_client.py`

#### `get_metadata_by_id(metadata_id)`

Mengambil metadata dari copyright-metadata-service.

#### `enrich_internal_results(internal_results)`

Menambahkan detail metadata ke hasil internal.

Alasannya:
- Milvus hanya tahu `metadata_id`;
- frontend butuh judul, kategori, image URL, dan informasi karya.

### `schemas/response_schema.py`

#### `WebMatchItem`

Schema kandidat eksternal dari web search.

#### `SimilarityRequest`

Schema request similarity check.

#### `EmbeddingInsertRequest`

Schema request insert embedding ke Milvus.

### Script Milvus

#### `create_milvus_collection.py`

Membuat collection Milvus dengan schema yang sesuai.

#### `insert_internal_images.py`

Memasukkan dataset gambar internal awal ke Milvus.

Fungsi penting:
- `connect_milvus`;
- `get_image_files`;
- `extract_feature`;
- `insert_images_to_milvus`.
