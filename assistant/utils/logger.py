import logging
import sys

def configure_logging():
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s"
    )

    file_handler = logging.FileHandler("app.log", mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger("assistant").setLevel(logging.DEBUG)
    logging.getLogger("infra").setLevel(logging.DEBUG)
    logging.getLogger("mem1").setLevel(logging.DEBUG)
