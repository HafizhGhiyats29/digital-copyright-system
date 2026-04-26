from pymilvus import connections, Collection, utility  # Client Milvus ORM
from config.settings import settings  # Import konfigurasi YAML
from utils.logger import logger  # Import logger


MILVUS_HOST = settings["milvus_host"]  # Host Milvus
MILVUS_PORT = settings["milvus_port"]  # Port Milvus
COLLECTION_NAME = settings["milvus_collection_name"]  # Nama collection internal
CLIP_FIELD = settings["clip_vector_field"]  # Nama field vector CLIP
CNN_FIELD = settings["cnn_vector_field"]  # Nama field vector CNN
METRIC_TYPE = settings["milvus_search_metric"]  # Metric similarity Milvus


def get_collection():  # Fungsi mengambil collection Milvus
    connections.connect(  # Membuat koneksi ke Milvus
        alias="default",  # Nama alias koneksi
        host=MILVUS_HOST,  # Host Milvus
        port=MILVUS_PORT  # Port Milvus
    )  # Menutup koneksi

    if not utility.has_collection(COLLECTION_NAME):  # Cek apakah collection ada
        logger.warning(f"Milvus collection tidak ditemukan: {COLLECTION_NAME}")  # Log jika collection belum ada
        return None  # Return None agar service tidak crash

    collection = Collection(COLLECTION_NAME)  # Ambil collection berdasarkan nama
    collection.load()  # Load collection ke memory agar bisa search

    return collection  # Return collection


def search_single_vector(collection, query_embedding, vector_field, top_k):  # Search satu jenis vector di Milvus
    search_params = {  # Parameter search Milvus
        "metric_type": METRIC_TYPE,  # Metric harus sama dengan index
        "params": {"nprobe": 10}  # Parameter IVF search
    }  # Menutup dictionary params

    results = collection.search(  # Melakukan vector search
        data=[query_embedding],  # Query embedding dalam bentuk list of vector
        anns_field=vector_field,  # Field vector yang dicari
        param=search_params,  # Parameter search
        limit=top_k,  # Jumlah hasil teratas
        output_fields=[  # Metadata yang ingin dikembalikan
            "image_id",  # ID gambar internal
            "image_url",  # URL/lokasi gambar internal
            "title",  # Judul/nama asset
            "owner",  # Pemilik organisasi/departemen
        ]  # Menutup output_fields
    )  # Menutup search

    output = []  # List hasil search

    for hit in results[0]:  # Loop hasil top-k
        entity = hit.entity  # Ambil entity metadata

        output.append({  # Simpan hasil dalam format dictionary
            "id": hit.id,  # Primary key Milvus
            "score": float(hit.score),  # Score dari Milvus
            "image_id": entity.get("image_id"),  # Metadata image_id
            "image_url": entity.get("image_url"),  # Metadata image_url
            "title": entity.get("title"),  # Metadata title
            "owner": entity.get("owner")  # Metadata owner
        })  # Menutup dictionary hasil

    return output  # Return list hasil


def merge_internal_results(clip_results, cnn_results):  # Gabungkan hasil CLIP dan CNN berdasarkan id
    merged = {}  # Dictionary untuk merge berdasarkan id

    for item in clip_results:  # Loop hasil CLIP
        item_id = item["id"]  # Ambil id
        merged[item_id] = {  # Buat data awal
            **item,  # Copy metadata
            "clip_score": item["score"],  # Simpan score CLIP
            "cnn_score": 0.0  # Default CNN score
        }  # Menutup dictionary

    for item in cnn_results:  # Loop hasil CNN
        item_id = item["id"]  # Ambil id

        if item_id not in merged:  # Jika belum ada dari hasil CLIP
            merged[item_id] = {  # Buat data baru
                **item,  # Copy metadata
                "clip_score": 0.0,  # Default CLIP score
                "cnn_score": item["score"]  # Simpan CNN score
            }  # Menutup dictionary
        else:  # Jika sudah ada dari hasil CLIP
            merged[item_id]["cnn_score"] = item["score"]  # Update CNN score

    return list(merged.values())  # Return hasil merge sebagai list


def search_internal_similarity(query_clip_embedding, query_cnn_embedding, top_k=3):  # Fungsi utama internal search
    collection = get_collection()  # Ambil collection Milvus

    if collection is None:  # Jika collection tidak tersedia
        return []  # Return kosong agar pipeline tetap jalan

    clip_results = search_single_vector(  # Search berdasarkan CLIP
        collection=collection,  # Collection Milvus
        query_embedding=query_clip_embedding,  # Query CLIP original
        vector_field=CLIP_FIELD,  # Field CLIP di Milvus
        top_k=top_k  # Jumlah hasil
    )  # Menutup search CLIP

    cnn_results = search_single_vector(  # Search berdasarkan CNN
        collection=collection,  # Collection Milvus
        query_embedding=query_cnn_embedding,  # Query CNN original
        vector_field=CNN_FIELD,  # Field CNN di Milvus
        top_k=top_k  # Jumlah hasil
    )  # Menutup search CNN

    merged_results = merge_internal_results(clip_results, cnn_results)  # Gabung hasil CLIP dan CNN

    clip_weight = settings["clip_weight"]  # Bobot CLIP
    cnn_weight = settings["cnn_weight"]  # Bobot CNN

    final_results = []  # List hasil akhir

    for item in merged_results:  # Loop hasil gabungan
        final_score = (item["clip_score"] * clip_weight) + (item["cnn_score"] * cnn_weight)  # Hitung final score

        final_results.append({  # Tambahkan hasil final
            "source": "internal",  # Sumber internal organisasi
            "final_score": float(final_score),  # Score akhir
            "clip_score": float(item["clip_score"]),  # Score CLIP
            "cnn_score": float(item["cnn_score"]),  # Score CNN
            "image_id": item.get("image_id"),  # Metadata image_id
            "image_url": item.get("image_url"),  # Metadata image_url
            "title": item.get("title"),  # Metadata title
            "owner": item.get("owner")  # Metadata owner
        })  # Menutup dictionary

    final_results = sorted(  # Urutkan hasil internal
        final_results,  # Data hasil
        key=lambda x: x["final_score"],  # Berdasarkan final_score
        reverse=True  # Tertinggi ke terendah
    )  # Menutup sorted

    return final_results[:top_k]  # Return top-k internal