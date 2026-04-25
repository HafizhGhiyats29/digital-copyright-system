import numpy as np  # Library untuk operasi vector


def cosine_similarity(vec1, vec2):  # Fungsi menghitung cosine similarity dua vector
    vec1 = np.array(vec1, dtype=np.float32)  # Ubah vector pertama ke numpy array float32
    vec2 = np.array(vec2, dtype=np.float32)  # Ubah vector kedua ke numpy array float32

    if vec1.shape != vec2.shape:  # Cek apakah dimensi vector sama
        return 0.0  # Jika dimensi beda, similarity dianggap 0

    dot_product = np.dot(vec1, vec2)  # Hitung dot product dua vector
    norm_a = np.linalg.norm(vec1)  # Hitung panjang vector pertama
    norm_b = np.linalg.norm(vec2)  # Hitung panjang vector kedua

    if norm_a == 0 or norm_b == 0:  # Cegah pembagian dengan nol
        return 0.0  # Jika salah satu vector nol, return 0

    similarity = dot_product / (norm_a * norm_b)  # Hitung cosine similarity

    return float(similarity)  # Return similarity sebagai float Python


def compute_external_similarity(query_clip_embedding, query_cnn_embedding, matches):  # Hitung similarity eksternal
    results = []  # Menampung semua hasil similarity

    clip_weight = 0.4  # Bobot CLIP untuk makna/semantic visual
    cnn_weight = 0.6  # Bobot CNN untuk detail visual gambar

    for match in matches:  # Loop semua kandidat hasil web-search
        match_data = match.model_dump() if hasattr(match, "model_dump") else match  # Ubah Pydantic object ke dict jika perlu

        candidate_clip_embedding = match_data.get("clip_embedding")  # Ambil embedding CLIP kandidat
        candidate_cnn_embedding = match_data.get("cnn_embedding")  # Ambil embedding CNN kandidat

        if not candidate_clip_embedding or not candidate_cnn_embedding:  # Cek embedding kandidat lengkap
            continue  # Lewati kandidat jika embedding tidak lengkap

        clip_score = cosine_similarity(query_clip_embedding, candidate_clip_embedding)  # Hitung similarity CLIP
        cnn_score = cosine_similarity(query_cnn_embedding, candidate_cnn_embedding)  # Hitung similarity CNN

        final_score = (clip_score * clip_weight) + (cnn_score * cnn_weight)  # Gabungkan skor CLIP dan CNN

        results.append({  # Tambahkan hasil similarity ke list
            "source": "external",  # Sumber hasil berasal dari internet/web
            "final_score": float(final_score),  # Skor akhir gabungan CLIP + CNN
            "clip_score": float(clip_score),  # Skor similarity berbasis CLIP
            "cnn_score": float(cnn_score),  # Skor similarity berbasis CNN
            "image_url": match_data.get("image_url"),  # URL gambar kandidat
            "title": match_data.get("title"),  # Judul kandidat
            "source_url": match_data.get("source_url")  # URL sumber kandidat
        })  # Menutup dictionary hasil

    return results  # Mengembalikan list hasil similarity