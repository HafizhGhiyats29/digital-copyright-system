import logging  # library logging

logging.basicConfig(
    level=logging.INFO,  # level log
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"  # format log
)

logger = logging.getLogger("upload-service")  # membuat logger