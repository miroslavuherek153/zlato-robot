import logging
import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/robot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_info(msg):
    logging.info(msg)
    print(msg)

def log_error(msg):
    logging.error(msg)
    print("ERROR:", msg)
