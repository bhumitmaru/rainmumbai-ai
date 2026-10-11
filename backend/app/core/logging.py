import logging
import sys
from pathlib import Path

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    log_dir = settings.project_root / "backend" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root.addHandler(stream)
    root.addHandler(file_handler)
