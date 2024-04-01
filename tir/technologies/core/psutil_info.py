import psutil
from tir.technologies.core.logging_config import logger

def system_info():
    logger().debug(f"CPU USAGE: {psutil.cpu_percent()}%")
    logger().debug(f"MEMORY USAGE: {psutil.virtual_memory().percent}%")
    logger().debug(f"MEMORY AVAILABLE: {round(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total, 2)}%")

if __name__ == "__main__":
    system_info()