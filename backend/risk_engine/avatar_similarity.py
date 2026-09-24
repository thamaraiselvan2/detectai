"""Local perceptual avatar comparison with conservative failure behavior."""

from functools import lru_cache
from io import BytesIO
import hashlib
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, ImageStat

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HASH_SIZE = 16
_MAX_IMAGE_BYTES = 8 * 1024 * 1024
_MAX_HAMMING_DISTANCE = 24
_MAX_COLOR_DISTANCE = 72


def _read_image(source):
    if not source:
        return None

    parsed = urlparse(str(source))
    try:
        if parsed.scheme in {"http", "https"}:
            request = Request(str(source), headers={"User-Agent": "DetectAI/1.0"})
            with urlopen(request, timeout=3) as response:
                data = response.read(_MAX_IMAGE_BYTES + 1)
            if len(data) > _MAX_IMAGE_BYTES:
                return None
            return Image.open(BytesIO(data))

        local_path = parsed.path if parsed.scheme == "file" else str(source)
        if local_path.startswith("/static/"):
            local_path = os.path.join(_BACKEND_DIR, local_path.lstrip("/"))
        elif not os.path.isabs(local_path):
            local_path = os.path.join(_BACKEND_DIR, local_path)
        if not os.path.isfile(local_path) or os.path.getsize(local_path) > _MAX_IMAGE_BYTES:
            return None
        with open(local_path, "rb") as handle:
            return Image.open(BytesIO(handle.read()))
    except (OSError, ValueError):
        return None


def _perceptual_hash(source):
    image = _read_image(source)
    if image is None:
        return None
    try:
        image = ImageOps.fit(
            image.convert("L"),
            (_HASH_SIZE, _HASH_SIZE),
            method=Image.Resampling.LANCZOS,
        )
        pixels = list(image.getdata())
        average = sum(pixels) / len(pixels)
        bits = "".join("1" if pixel >= average else "0" for pixel in pixels)
        color_means = tuple(ImageStat.Stat(image.convert("RGB")).mean)
        return int(bits, 2), color_means
    except (OSError, ValueError):
        return None


@lru_cache(maxsize=256)
def _cached_hash(source):
    return _perceptual_hash(source)


def are_similar_avatars(first_source, second_source):
    """Return True only when both images can be read and their hashes are close."""
    if not first_source or not second_source:
        return False
    if str(first_source) == str(second_source):
        return _cached_hash(str(first_source)) is not None

    first_hash = _cached_hash(str(first_source))
    second_hash = _cached_hash(str(second_source))
    if first_hash is None or second_hash is None:
        return False
    hamming_distance = (first_hash[0] ^ second_hash[0]).bit_count()
    color_distance = sum((first - second) ** 2 for first, second in zip(first_hash[1], second_hash[1])) ** 0.5
    return hamming_distance <= _MAX_HAMMING_DISTANCE and color_distance <= _MAX_COLOR_DISTANCE
