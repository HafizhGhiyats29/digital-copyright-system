# digital-copyright-system

tutorial clone sampe push

1. git clone https://github.com/HafizhGhiyats29/digital-copyright-system.git
2. cd digital-copyright-system
3. git checkout -b main
4. git pull origin main (untuk cek ada code terbaru)
5. sebelum git add . , coba tambahin kode di format file .py mana saja contoh di file app.py tambahin code print("hello world")
6. git add .
7. git commit -m "tulis pesan perubahan"
8. git remote -v (buat pastiin dah terhubung sama link remotenya)
9. git push -u origin main

tutorial run feature extraction secara lokal

1. buka terminal cmd
2. masuk kedalam folder feature extraction cd fea.....
3. ketik code . di cmd
4. ketik python -m venv venv
5. ketik venv\Scripts\activate
6. ketik pip install -r requirements.txt
7. ketik uvicorn app:app --reload --host 0.0.0.0 --port 8001
8. masuk ke web browser di search engine ketik http://localhost:8001/docs
9. expan extract endpoin klik try it out
10. masukin ajh gambar tunggu hasil embedding
