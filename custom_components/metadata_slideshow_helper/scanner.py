from __future__ import annotations

import contextlib
import logging
import os
from dataclasses import dataclass

import exifread
import piexif
from PIL import Image

# Suppress exifread warnings for unrecognized formats
logging.getLogger("exifread").setLevel(logging.ERROR)

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
        if not os.path.isdir(self.root):
            # TODO: Log warning
            return results

        # TODO: Check if pathlib glob
        for dirpath, _, filenames in os.walk(self.root):
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in SUPPORTED_EXT:
                    continue
                full = os.path.join(dirpath, fn)

                # Skip unreadable files (broken symlinks, permission issues)
                if not os.path.isfile(full) or not os.access(full, os.R_OK):
                    continue

                try:
                    meta = self._read_metadata(full)
                    results.append(meta)
                except Exception:
                    # Skip files that can't be read at all
                    results.append(ImageMeta(path=full, tags=[], rating=0, date=None))
        return results

    def _read_metadata(self, path: str) -> ImageMeta:
        tags: list[str] = []
        rating = 0
        date = None
        ext = os.path.splitext(path)[1].lower()

        # Try to read XMP (embedded) via Pillow (requires defusedxml)
        try:
            with Image.open(path) as im:
                xmp_raw = im.getxmp()
            if isinstance(xmp_raw, dict):
                # Pillow with defusedxml returns nested dict: {'xmpmeta': {'RDF': {'Description': {...}}}}
                desc = xmp_raw.get("xmpmeta", {}).get("RDF", {}).get("Description", {})
                if desc:
                    # Extract tags from subject/Bag/li
                    subj_bag = desc.get("subject", {}).get("Bag", {}).get("li")
                    if isinstance(subj_bag, list):
                        tags = [str(t) for t in subj_bag]
                    elif isinstance(subj_bag, str):
                        tags = [subj_bag]

                    # Extract rating
                    rate = desc.get("Rating")
                    if isinstance(rate, (int, str)):
                        with contextlib.suppress(ValueError):
                            rating = int(rate)
        except Exception:
            pass
        # Only try to read EXIF from JPEG files
        if ext in {".jpg", ".jpeg"}:
            # Verify file is accessible and readable
            if not os.path.isfile(path) or not os.access(path, os.R_OK):
                return ImageMeta(path=path, tags=tags, rating=rating, date=date)

            try:
                with open(path, "rb") as f:
                    exif_tags = exifread.process_file(
                        f, details=False, stop_tag="EXIF DateTimeOriginal"
                    )
                    raw_date = exif_tags.get("EXIF DateTimeOriginal") or exif_tags.get(
                        "Image DateTime"
                    )
                    date = str(raw_date) if raw_date else None
            except Exception:
                pass  # Silently skip EXIF read errors

            try:
                exif_dict = piexif.load(path)
                xmp_rating = exif_dict.get("0th", {}).get(piexif.ImageIFD.Rating)
                if isinstance(xmp_rating, int):
                    rating = xmp_rating
            except Exception:
                pass  # Silently skip piexif errors

        return ImageMeta(path=path, tags=tags, rating=rating or 0, date=date)


def apply_filters(
    items: list[ImageMeta], include_tags: list[str], exclude_tags: list[str], min_rating: int
) -> list[ImageMeta]:
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
