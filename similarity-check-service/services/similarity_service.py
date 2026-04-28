from services.cosine_service import compute_external_similarity  # import cosine


async def compute_similarity(query_embedding, web_matches):

    # 🔥 hitung similarity
    results = compute_external_similarity(query_embedding, web_matches)

    # 🔥 sorting (ranking dari paling mirip)
    results = sorted(
        results,
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results