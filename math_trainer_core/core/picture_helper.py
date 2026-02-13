from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen


_DEFAULT_CACHE_DIR = Path(".picture_cache")
_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class PictureRef:
    url: str


def download_picture(
    picture: PictureRef, cache_dir: Path = _DEFAULT_CACHE_DIR
) -> Path:
    """
    Ensure the picture is downloaded into cache_dir.
    Cache filename is derived from URL hash + URL extension.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    final_path = _cache_path_for_url(picture.url, cache_dir)
    if final_path.exists():
        return final_path

    temp_path = _download_to_temp(picture.url, cache_dir, final_path.suffix)
    final_path = _finalize_download(temp_path, final_path)
    return final_path


def _cache_path_for_url(url: str, cache_dir: Path) -> Path:
    extension = _extension_from_url(url)
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{url_hash}{extension}"


def _extension_from_url(url: str) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix
    if not suffix:
        raise ValueError(f"URL has no extension: {url!r}")
    return suffix


def _download_to_temp(url: str, cache_dir: Path, extension: str) -> Path:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=cache_dir,
            suffix=extension,
        ) as tmp_file:
            temp_path = Path(tmp_file.name)
            request = Request(url, headers={"User-Agent": _DEFAULT_USER_AGENT})
            with urlopen(request, timeout=20) as response:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    tmp_file.write(chunk)
        return temp_path
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def _finalize_download(temp_path: Path, expected_path: Path) -> Path:
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    if expected_path.exists():
        temp_path.unlink(missing_ok=True)
        return expected_path
    temp_path.replace(expected_path)
    return expected_path
