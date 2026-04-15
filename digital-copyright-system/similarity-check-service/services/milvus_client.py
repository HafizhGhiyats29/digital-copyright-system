# from pymilvus import connections, Collection  # milvus

# # connect ke milvus
# connections.connect("default", host="localhost", port="19530")

# collection = Collection("image_embeddings")  # nama collection


# def search_milvus(query_embedding):

#     results = collection.search(
#         data=[query_embedding],
#         anns_field="embedding",
#         param={"metric_type": "COSINE"},
#         limit=5
#     )

#     output = []

#     for hit in results[0]:
#         output.append({
#             "source": "internal",
#             "similarity": hit.score,
#             "id": hit.id
#         })

#     return output