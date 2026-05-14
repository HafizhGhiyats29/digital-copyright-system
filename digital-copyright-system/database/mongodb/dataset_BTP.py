import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["BTP"]
collection = db["Dokumen_Image"]

df = pd.read_excel("Dataset BTP.xlsx")

# bersihin data kosong
df = df.dropna(how="all")

# hapus kolom yang gak dipakai
df = df.drop(columns=["ki_id", "Link Contoh Ciptaan", "Contoh Ciptaan"], errors="ignore")

print("Jumlah data:", len(df))
print("Kolom:", df.columns)

data = df.to_dict(orient="records")

collection.delete_many({})
collection.insert_many(data)

print("Data berhasil masuk ke database")
print(len(df))
print(df.head())