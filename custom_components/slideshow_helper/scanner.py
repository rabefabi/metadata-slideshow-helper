from __future__ import annotations

import os
from dataclasses import dataclass

import exifread
import piexif
from PIL import Image  # noqa: F401 (placeholder for future use)

SUPPORTED_EXT = {".jpg", ".jpeg", ".png"}

@dataclass
class ImageMeta:
    path: str
    tags: list[str]
    rating: int
    date: str | None

class MediaScanner:
    def __init__(self, root: str):
        self.root = root

    def scan(self) -> list[ImageMeta]:
        results: list[ImageMeta] = []
        for dirpath, _, filenames in os.walk(self.root):
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in SUPPORTED_EXT:
                    continue
                full = os.path.join(dirpath, fn)
                try:
                    meta = self._read_metadata(full)
                    results.append(meta)
                except Exception:
                    results.append(ImageMeta(path=full, tags=[], rating=0, date=None))
        return results

    def _read_metadata(self, path: str) -> ImageMeta:
        tags: list[str] = []
        rating = 0
        date = None
        ext = os.path.splitext(path)[1].lower()
        if ext in {".jpg", ".jpeg"}:
            try:
                with open(path, "rb") as f:
                    exif_tags = exifread.process_file(f, details=False)
                    raw_date = exif_tags.get("EXIF DateTimeOriginal") or exif_tags.get("Image DateTime")
                    date = str(raw_date) if raw_date else None
            except Exception:
                pass
            try:
                exif_dict = piexif.load(path)
                xmp_rating = exif_dict.get("0th", {}).get(piexif.ImageIFD.Rating)
                if isinstance(xmp_rating, int):
                    rating = xmp_rating
            except Exception:
                pass
        return ImageMeta(path=path, tags=tags, rating=rating or 0, date=date)


def apply_filters(items: list[ImageMeta], include_tags: list[str], exclude_tags: list[str], min_rating: int) -> list[ImageMeta]:
    inc = set(t.lower() for t in include_tags or [])
    exc = set(t.lower() for t in exclude_tags or [])
    out: list[ImageMeta] = []
    for it in items:
        tset = set(s.lower() for s in it.tags)
        if inc and not inc.issubset(tset):
            continue
        if exc and tset.intersection(exc):
            continue
        if (it.rating or 0) < (min_rating or 0):
            continue
        out.append(it)
    return out
