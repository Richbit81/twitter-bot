from __future__ import annotations

import mimetypes
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def resolve_image_path(image: str, root: Path = ROOT_DIR) -> Path:
    path = Path(image)
    if path.is_absolute() and path.exists():
        return path

    local = root / image
    if local.exists():
        return local

    if image.startswith(("http://", "https://")):
        return download_image(image)

    raise FileNotFoundError(f"Image not found: {image}")


def download_image(url: str) -> Path:
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    suffix = _suffix_from_response(url, response.headers.get("Content-Type", ""))
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp.write(response.content)
    temp.close()
    return Path(temp.name)


def _suffix_from_response(url: str, content_type: str) -> str:
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return ext

    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
    if guessed in SUPPORTED_EXTENSIONS:
        return guessed

    return ".png"
