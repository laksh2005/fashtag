from __future__ import annotations

import hashlib
import mimetypes
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from scraper.config import (
    DEFAULT_DOWNLOAD_DELAY_SECONDS,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)


class ImageDownloadError(RuntimeError):
    """Raised when an image cannot be downloaded or validated."""


def image_id_from_url(image_url: str) -> str:
    return hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:16]


def _extension_from_response(image_url: str, content_type: str | None) -> str:
    if content_type:
        extension = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if extension in {".jpg", ".jpeg", ".png", ".webp"}:
            return ".jpg" if extension == ".jpeg" else extension

    parsed_path = urlparse(image_url).path
    suffix = Path(parsed_path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix

    return ".jpg"


def download_image(
    image_url: str,
    destination_dir: Path,
    *,
    timeout_seconds: int = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    delay_seconds: float = DEFAULT_DOWNLOAD_DELAY_SECONDS,
) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"}

    try:
        response = requests.get(image_url, headers=headers, timeout=timeout_seconds)
    except requests.RequestException as exc:
        raise ImageDownloadError(f"request failed: {exc}") from exc

    if response.status_code != 200:
        raise ImageDownloadError(f"unexpected status code: {response.status_code}")

    content_type = response.headers.get("content-type", "")
    if "image" not in content_type.lower():
        raise ImageDownloadError(f"not an image response: {content_type}")

    extension = _extension_from_response(image_url, content_type)
    image_path = destination_dir / f"{image_id_from_url(image_url)}{extension}"

    if image_path.exists() and image_path.stat().st_size > 0:
        return image_path

    image_path.write_bytes(response.content)
    time.sleep(delay_seconds)

    if image_path.stat().st_size < 1024:
        image_path.unlink(missing_ok=True)
        raise ImageDownloadError("downloaded file is too small")

    return image_path
