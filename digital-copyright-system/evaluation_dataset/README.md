# Evaluation Dataset

Isi folder ini dengan gambar uji untuk menghitung akurasi CLIP/CNN.

Folder:
- same: pasangan gambar yang sama, termasuk resize/kompresi/thumbnail.
- different: gambar yang benar-benar berbeda.
- semantic_similar: gambar dengan konsep sama tapi bukan gambar yang sama, misalnya dua pohon digital berbeda.
- modified: gambar yang sama tapi dimodifikasi, misalnya crop, watermark, brightness, atau compression.

Edit pairs.csv agar path dan label sesuai dengan file gambar yang kamu masukkan.

Label yang didukung:
- plagiarized / same / copy / duplicate
- not_plagiarized / different / semantic_only

Contoh menjalankan:

cd "E:\Hafizh Code\Capstone2\digital-copyright-system"
.\feature-extraction-service\venv\Scripts\python.exe scripts\evaluate_similarity.py --pairs evaluation_dataset\pairs.csv
