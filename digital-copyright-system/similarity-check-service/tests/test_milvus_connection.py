from pymilvus import connections, utility  # Import koneksi dan utility Milvus

connections.connect(  # Membuat koneksi ke Milvus
    alias="default",  # Alias koneksi default
    host="localhost",  # Host Milvus dari Docker
    port="19530"  # Port Milvus
)  # Menutup koneksi

print("Connected to Milvus")  # Menampilkan status koneksi
print("Collections:", utility.list_collections())  # Menampilkan daftar collection