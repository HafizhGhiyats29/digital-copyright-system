import numpy as np  # operasi vector


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)  # ubah ke numpy
    vec2 = np.array(vec2)

    dot_product = np.dot(vec1, vec2)  # dot product
    norm_a = np.linalg.norm(vec1)  # panjang vector
    norm_b = np.linalg.norm(vec2)

    if norm_a == 0 or norm_b == 0:  # handle error
        return 0.0

    return dot_product / (norm_a * norm_b)  # cosine similarity


def compute_external_similarity(query_embedding, matches):
    results = []

    for m in matches:
        similarity = cosine_similarity(
            query_embedding,
            m["embedding"]
        )

        results.append({
            "source": "external",
            "similarity": float(similarity),
            "image_url": m.get("image_url"),
            "title": m.get("title"),
            "source_url": m.get("source_url")
        })

    return results