import logging  # Mengimpor modul logging bawaan Python


logging.basicConfig(  # Mengatur konfigurasi logging dasar
    level=logging.INFO,  # Menampilkan log mulai dari level INFO
    format="%(asctime)s | %(levelname)s | decision-engine | %(message)s"  # Format tampilan log
)  # Menutup konfigurasi logging


logger = logging.getLogger(__name__)  # Membuat object logger yang bisa diimport file lain