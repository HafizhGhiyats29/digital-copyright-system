from services.cosine_service import compute_external_similarity  # Import fungsi similarity eksternal


async def compute_similarity(query_clip_embedding, query_cnn_embedding, web_matches):  # Fungsi utama similarity
    results = compute_external_similarity(  # Hitung similarity CLIP + CNN
        query_clip_embedding,  # Embedding CLIP original
        query_cnn_embedding,  # Embedding CNN original
        web_matches  # Kandidat web dari web-search-service
    )  # Menutup pemanggilan fungsi

    results = sorted(  # Urutkan hasil similarity
        results,  # List hasil similarity
        key=lambda x: x["final_score"],  # Pakai final_score sebagai dasar ranking
        reverse=True  # Urutkan dari skor terbesar ke terkecil
    )  # Menutup sorted

    return results  # Mengembalikan hasil ranking