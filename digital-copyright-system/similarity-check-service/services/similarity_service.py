from services.cosine_service import compute_external_similarity  # Mengimpor fungsi similarity eksternal berbasis cosine
from services.metadata_client import enrich_internal_results  # Mengambil detail metadata untuk hasil internal
from services.milvus_client import search_internal_similarity  # Mengimpor fungsi similarity internal berbasis Milvus
from config.settings import settings  # Mengimpor konfigurasi dari settings.yaml


def sort_by_score(results):  # Fungsi untuk mengurutkan hasil berdasarkan final_score
    return sorted(  # Mengembalikan list yang sudah diurutkan
        results,  # Data hasil similarity
        key=lambda item: item.get("final_score", 0.0),  # Mengambil final_score sebagai dasar sorting
        reverse=True  # Mengurutkan dari skor terbesar ke terkecil
    )  # Menutup fungsi sorted


def get_top_results(results, limit):  # Fungsi mengambil top-N hasil
    return results[:limit]  # Mengambil hasil sebanyak limit dari urutan teratas


def get_best_score(results):  # Fungsi mengambil skor terbaik dari satu list hasil
    if not results:  # Mengecek apakah list kosong
        return 0.0  # Mengembalikan 0 jika tidak ada hasil

    return float(results[0].get("final_score", 0.0))  # Mengambil final_score dari item ranking pertama


def build_final_response(internal_results, external_results):  # Fungsi membangun response akhir untuk frontend
    display_top_k = settings.get("display_top_k", 3)  # Mengambil jumlah data top yang akan ditampilkan

    internal_results = sort_by_score(internal_results)  # Mengurutkan hasil internal berdasarkan final_score
    external_results = sort_by_score(external_results)  # Mengurutkan hasil eksternal berdasarkan final_score

    combined_results = sort_by_score(  # Membuat ranking gabungan internal dan eksternal
        internal_results + external_results  # Menggabungkan dua list hasil
    )  # Menutup sorting gabungan

    best_internal_score = get_best_score(internal_results)  # Mengambil skor internal terbaik
    best_external_score = get_best_score(external_results)  # Mengambil skor eksternal terbaik

    if not combined_results:  # Mengecek jika tidak ada hasil sama sekali
        return {  # Mengembalikan response kosong
            "overall_score": 0.0,  # Skor utama bernilai 0
            "best_source": None,  # Tidak ada sumber terbaik
            "best_match": None,  # Tidak ada kandidat terbaik
            "summary": {  # Ringkasan hasil
                "best_internal_score": best_internal_score,  # Skor internal terbaik
                "best_external_score": best_external_score,  # Skor eksternal terbaik
                "internal_total": 0,  # Total hasil internal
                "external_total": 0,  # Total hasil eksternal
                "combined_total": 0  # Total hasil gabungan
            },  # Menutup summary
            "results": {  # Detail hasil
                "internal_top3": [],  # Top 3 internal kosong
                "external_top3": [],  # Top 3 eksternal kosong
                "combined_top3": []  # Top 3 gabungan kosong
            }  # Menutup results
        }  # Menutup response kosong

    best_match = combined_results[0]  # Mengambil kandidat dengan skor tertinggi dari semua sumber
    overall_score = float(best_match.get("final_score", 0.0))  # Mengambil final_score tertinggi sebagai overall_score
    best_source = best_match.get("source")  # Mengambil sumber kandidat terbaik, internal atau external

    return {  # Mengembalikan response ideal untuk frontend
        "overall_score": overall_score,  # Skor utama yang akan ditampilkan besar di frontend
        "best_source": best_source,  # Sumber dari skor terbaik
        "best_match": best_match,  # Detail kandidat terbaik
        "summary": {  # Ringkasan hasil similarity
            "best_internal_score": best_internal_score,  # Skor internal tertinggi
            "best_external_score": best_external_score,  # Skor eksternal tertinggi
            "internal_total": len(internal_results),  # Jumlah hasil internal
            "external_total": len(external_results),  # Jumlah hasil eksternal
            "combined_total": len(combined_results)  # Jumlah hasil gabungan
        },  # Menutup summary
        "results": {  # Data detail untuk frontend
            "internal_top3": get_top_results(internal_results, display_top_k),  # Top 3 hasil internal
            "external_top3": get_top_results(external_results, display_top_k),  # Top 3 hasil eksternal
            "combined_top3": get_top_results(combined_results, display_top_k)  # Top 3 hasil gabungan
        }  # Menutup results
    }  # Menutup response


async def compute_similarity(query_clip_embedding, query_cnn_embedding, web_matches):  # Fungsi utama similarity check
    internal_results = search_internal_similarity(  # Mencari kemiripan internal menggunakan Milvus
        query_clip_embedding=query_clip_embedding,  # Embedding CLIP gambar input
        query_cnn_embedding=query_cnn_embedding,  # Embedding CNN gambar input
        top_k=settings.get("top_k_internal", 10)  # Jumlah kandidat internal yang diambil
    )  # Menutup pemanggilan Milvus

    internal_results = await enrich_internal_results(internal_results)  # Tambahkan detail metadata dan saring data belum ready

    external_results = compute_external_similarity(  # Menghitung similarity eksternal menggunakan cosine manual
        query_clip_embedding,  # Embedding CLIP gambar input
        query_cnn_embedding,  # Embedding CNN gambar input
        web_matches  # Kandidat dari web-search-service
    )  # Menutup pemanggilan external similarity

    external_results = sort_by_score(external_results)  # Mengurutkan hasil eksternal
    external_results = external_results[:settings.get("top_k_external", 10)]  # Membatasi hasil eksternal yang dipakai

    final_response = build_final_response(  # Membuat format response akhir
        internal_results,  # Hasil internal dari Milvus
        external_results  # Hasil eksternal dari cosine manual
    )  # Menutup build response

    return final_response  # Mengembalikan response final ke route