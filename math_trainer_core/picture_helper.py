from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen


_DEFAULT_CACHE_DIR = Path(".picture_cache")


class PictureError(Exception):
    pass


class PictureHashMismatchError(PictureError):
    def __init__(self, expected_sha256: str, actual_sha256: str, actual_path: Path):
        message = (
            "Picture sha256 mismatch. "
            f"Expected {expected_sha256}, got {actual_sha256}. "
            f"Renamed to {actual_path}."
        )
        super().__init__(message)
        self.expected_sha256 = expected_sha256
        self.actual_sha256 = actual_sha256
        self.actual_path = actual_path


@dataclass(frozen=True)
class PictureRef:
    url: str
    sha256: str


def download_picture(
    picture: PictureRef, cache_dir: Path = _DEFAULT_CACHE_DIR
) -> Path:
    """
    Ensure the picture is downloaded into cache_dir as <sha256>.<extension>.

    Returns the cached file path on success. Raises PictureHashMismatchError if
    the downloaded content does not match the expected sha256 (and renames the
    file to the correct sha256 before raising).
    """
    expected_sha = _normalize_sha256(picture.sha256)
    extension = _extension_from_url(picture.url)

    cache_dir.mkdir(parents=True, exist_ok=True)
    expected_path = cache_dir / f"{expected_sha}{extension}"

    if expected_path.exists():
        actual_sha = _sha256_file(expected_path)
        if actual_sha != expected_sha:
            actual_path = _rename_to_actual_sha(expected_path, actual_sha, extension)
            raise PictureHashMismatchError(expected_sha, actual_sha, actual_path)
        return expected_path

    temp_path = _download_to_temp(picture.url, cache_dir, extension)
    actual_sha = _sha256_file(temp_path)
    if actual_sha != expected_sha:
        actual_path = _rename_to_actual_sha(temp_path, actual_sha, extension)
        raise PictureHashMismatchError(expected_sha, actual_sha, actual_path)

    return _finalize_download(temp_path, expected_path)


def _normalize_sha256(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(c not in "0123456789abcdef" for c in normalized):
        raise ValueError(f"Invalid sha256: {value!r}")
    return normalized


def _extension_from_url(url: str) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix
    if not suffix:
        raise ValueError(f"URL has no extension: {url!r}")
    return suffix


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _download_to_temp(url: str, cache_dir: Path, extension: str) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        delete=False,
        dir=cache_dir,
        suffix=extension,
    ) as tmp_file:
        with urlopen(url) as response:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                tmp_file.write(chunk)
        return Path(tmp_file.name)


def _finalize_download(temp_path: Path, expected_path: Path) -> Path:
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.replace(expected_path)
    return expected_path


def _rename_to_actual_sha(path: Path, actual_sha: str, extension: str) -> Path:
    actual_path = path.parent / f"{actual_sha}{extension}"
    if actual_path.exists():
        path.unlink(missing_ok=True)
        return actual_path
    path.replace(actual_path)
    return actual_path
