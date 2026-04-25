import logging  # Modul logging bawaan Python


logging.basicConfig(  # Konfigurasi logging
    level=logging.INFO,  # Level minimum log
    format="%(asctime)s | %(levelname)s | feature-service | %(message)s"  # Format log
)  # Menutup konfigurasi logging


logger = logging.getLogger(__name__)  # Membuat logger untuk file aktif