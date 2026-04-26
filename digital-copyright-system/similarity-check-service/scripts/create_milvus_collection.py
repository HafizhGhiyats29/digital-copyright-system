from pymilvus import connections  # Import koneksi Milvus
from pymilvus import utility  # Import utility untuk cek collection
from pymilvus import FieldSchema  # Import schema field Milvus
from pymilvus import CollectionSchema  # Import schema collection Milvus
from pymilvus import DataType  # Import tipe data Milvus
from pymilvus import Collection  # Import Collection Milvus
from config.settings import settings  # Import settings dari file config


COLLECTION_NAME = settings["milvus_collection_name"]  # Ambil nama collection dari settings.yaml
MILVUS_HOST = settings["milvus_host"]  # Ambil host Milvus dari settings.yaml
MILVUS_PORT = settings["milvus_port"]  # Ambil port Milvus dari settings.yaml


connections.connect(  # Membuat koneksi ke Milvus
    alias="default",  # Nama alias koneksi default
    host=MILVUS_HOST,  # Host Milvus
    port=MILVUS_PORT  # Port Milvus
)  # Menutup koneksi Milvus


if utility.has_collection(COLLECTION_NAME):  # Cek apakah collection sudah ada
    print(f"Collection '{COLLECTION_NAME}' sudah ada")  # Tampilkan info jika collection sudah ada
    collection = Collection(COLLECTION_NAME)  # Ambil collection yang sudah ada
    print(collection.describe())  # Tampilkan detail collection
    exit()  # Hentikan script agar tidak membuat ulang collection


id_field = FieldSchema(  # Membuat field primary key
    name="id",  # Nama field primary key
    dtype=DataType.INT64,  # Tipe data integer 64-bit
    is_primary=True,  # Menandakan field ini sebagai primary key
    auto_id=True  # ID dibuat otomatis oleh Milvus
)  # Menutup field id


image_id_field = FieldSchema(  # Membuat field image_id
    name="image_id",  # Nama field image_id
    dtype=DataType.VARCHAR,  # Tipe data string
    max_length=128  # Panjang maksimal string
)  # Menutup field image_id


image_url_field = FieldSchema(  # Membuat field image_url
    name="image_url",  # Nama field image_url
    dtype=DataType.VARCHAR,  # Tipe data string
    max_length=1024  # Panjang maksimal URL
)  # Menutup field image_url


title_field = FieldSchema(  # Membuat field title
    name="title",  # Nama field title
    dtype=DataType.VARCHAR,  # Tipe data string
    max_length=512  # Panjang maksimal title
)  # Menutup field title


owner_field = FieldSchema(  # Membuat field owner
    name="owner",  # Nama field owner
    dtype=DataType.VARCHAR,  # Tipe data string
    max_length=256  # Panjang maksimal owner
)  # Menutup field owner


clip_embedding_field = FieldSchema(  # Membuat field vector CLIP
    name=settings["clip_vector_field"],  # Nama field dari settings.yaml
    dtype=DataType.FLOAT_VECTOR,  # Tipe data vector float
    dim=512  # Dimensi CLIP ViT-B/32
)  # Menutup field CLIP


cnn_embedding_field = FieldSchema(  # Membuat field vector CNN
    name=settings["cnn_vector_field"],  # Nama field dari settings.yaml
    dtype=DataType.FLOAT_VECTOR,  # Tipe data vector float
    dim=2048  # Dimensi output ResNet50 tanpa FC layer
)  # Menutup field CNN


schema = CollectionSchema(  # Membuat schema collection
    fields=[  # Daftar field dalam collection
        id_field,  # Field primary key
        image_id_field,  # Field image_id
        image_url_field,  # Field image_url
        title_field,  # Field title
        owner_field,  # Field owner
        clip_embedding_field,  # Field vector CLIP
        cnn_embedding_field  # Field vector CNN
    ],  # Menutup daftar field
    description="Internal image embeddings for copyright similarity checking"  # Deskripsi collection
)  # Menutup schema collection


collection = Collection(  # Membuat collection baru
    name=COLLECTION_NAME,  # Nama collection
    schema=schema  # Schema collection
)  # Menutup pembuatan collection


index_params = {  # Parameter index vector
    "index_type": "IVF_FLAT",  # Jenis index Milvus
    "metric_type": settings["milvus_search_metric"],  # Metric similarity, misalnya COSINE
    "params": {"nlist": 128}  # Parameter index IVF
}  # Menutup index params


collection.create_index(  # Membuat index untuk CLIP embedding
    field_name=settings["clip_vector_field"],  # Nama field CLIP
    index_params=index_params  # Parameter index
)  # Menutup create index CLIP


collection.create_index(  # Membuat index untuk CNN embedding
    field_name=settings["cnn_vector_field"],  # Nama field CNN
    index_params=index_params  # Parameter index
)  # Menutup create index CNN


collection.load()  # Load collection ke memory agar siap untuk search


print(f"Collection '{COLLECTION_NAME}' berhasil dibuat")  # Tampilkan pesan sukses
print("Collections:", utility.list_collections())  # Tampilkan daftar collection
print(collection.describe())  # Tampilkan detail collection