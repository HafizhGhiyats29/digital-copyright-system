from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client["BTP"]
collection = db["Dokumen_Image"]

# ======================
# CRUD TAMBAHAN
# ======================

# CREATE
def create_metadata(data):
    return collection.insert_one(data)

# READ
def get_all_metadata():
    return list(collection.find())

# UPDATE
def update_metadata(id, data):
    return collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": data}
    )

# DELETE
def delete_metadata(id):
    return collection.delete_one(
        {"_id": ObjectId(id)}
    )