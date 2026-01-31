from __future__ import annotations

import contextlib
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

import exifread
import piexif
from PIL import Image

from .const import DEFAULT_RESCAN_INTERVAL

# Suppress exifread warnings for unrecognized formats
logging.getLogger("exifread").setLevel(logging.ERROR)

_LOGGER = logging.getLogger(__name__)

SUPPORTED_EXT = {".jpg", ".jpeg", ".png"}


WARN_COOLDOWN = 3600.0  # seconds (1 hour)


@dataclass
class ImageMeta:
    path: str
    tags: list[str]
    rating: int
    date: str | None


@dataclass
class ScanResult:
    """Result from scanning and filtering media."""

    discovered: list[ImageMeta]
    matching: list[ImageMeta]
    discovered_count: int
    matching_count: int


class MediaScanner:
    def __init__(
        self,
        roots: list[str],
        include_tags: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        min_rating: int = 0,
        rescan_interval: float = DEFAULT_RESCAN_INTERVAL,
    ):
        self.roots = roots
        self.include_tags = include_tags or []
        self.exclude_tags = exclude_tags or []
        self.min_rating = min_rating
        self.rescan_interval = rescan_interval
        self.cached_items: list[ImageMeta] = []
        self.last_scan: float = 0.0
        self.last_warn_time: float = 0.0
        self.warn_cooldown: float = WARN_COOLDOWN

    def scan_and_filter(self) -> ScanResult:
        """Scan media and apply configured filters, with caching and warnings.

        Returns:
            ScanResult with discovered and matching images and their counts.
        """
        current_time = time.time()

        # Only rescan filesystem periodically
        if not self.cached_items or (current_time - self.last_scan) >= float(self.rescan_interval):
            _LOGGER.info(f"Rescanning media_dirs: {self.roots}")
            discovered_items = self.scan()
            self.cached_items = discovered_items
            self.last_scan = current_time
        else:
            discovered_items = self.cached_items

        # Apply configured filters
        matching_items = apply_filters(
            discovered_items, self.include_tags, self.exclude_tags, self.min_rating
        )

        # Log warnings if no matches
        if not matching_items and (current_time - self.last_warn_time) >= self.warn_cooldown:
            _LOGGER.warning(
                f"No images matched filters in {self.roots} "
                f"(discovered {len(discovered_items)} images, min_rating={self.min_rating}, "
                f"include_tags={self.include_tags}, exclude_tags={self.exclude_tags})"
            )
            self.last_warn_time = current_time
        elif matching_items:
            # Reset warning cooldown when images are found
            self.last_warn_time = 0.0
            _LOGGER.debug(
                f"Found {len(matching_items)} matching images (from {len(discovered_items)} discovered)"
            )

        return ScanResult(
            discovered=discovered_items,
            matching=matching_items,
            discovered_count=len(discovered_items),
            matching_count=len(matching_items),
        )

    def scan(self) -> list[ImageMeta]:
        results: list[ImageMeta] = []

        for root in self.roots:
            root_path = Path(root)
            if not root_path.is_dir():
                _LOGGER.warning("Media root not found or not a directory: %s", root)
                continue

            for ext in SUPPORTED_EXT:
                for p in root_path.rglob(f"*{ext}"):
                    # Skip unreadable files (broken symlinks, permission issues)
                    if not p.is_file() or not os.access(p, os.R_OK):
                        continue

                    full = str(p)
                    try:
                        meta = self._read_metadata(full)
                        results.append(meta)
                    except Exception:
                        # On any error, still include the file with empty metadata
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
    discovered_items: list[ImageMeta],
    include_tags: list[str],
    exclude_tags: list[str],
    min_rating: int,
) -> list[ImageMeta]:
    """Filter discovered images based on tags and rating criteria.

    Args:
        discovered_items: List of all discovered images from the media scan.
        include_tags: Only include images with all of these tags (case-insensitive).
        exclude_tags: Exclude images with any of these tags (case-insensitive).
        min_rating: Only include images with rating >= min_rating.

    Returns:
        List of matching images that pass all filters.
    """
    inc = set(t.lower() for t in include_tags or [])
    exc = set(t.lower() for t in exclude_tags or [])
    matching: list[ImageMeta] = []
    for item in discovered_items:
        tset = set(s.lower() for s in item.tags)
        if inc and not inc.issubset(tset):
            continue
        if exc and tset.intersection(exc):
            continue
        if (item.rating or 0) < (min_rating or 0):
            continue
        matching.append(item)
    return matching
