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
    matching: list[ImageMeta] | None
    """matching is `None` if filtering was not applied"""
    failed_count: int
    non_image_file_count: int


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
        self.cached_scan_result: ScanResult | None = None
        self.last_scan: float = 0.0

    def scan_and_filter(self) -> ScanResult:
        """Scan media and apply configured filters, with caching and warnings.

        Returns:
            ScanResult with discovered and matching images and their counts.
        """
        current_time = time.time()

        # Only rescan filesystem periodically
        if not self.cached_scan_result or (current_time - self.last_scan) >= float(
            self.rescan_interval
        ):
            _LOGGER.info(f"Rescanning media_dirs: {self.roots}")
            self.cached_scan_result = self.scan()
            self.last_scan = current_time

        # Apply configured filters
        matching_items = apply_filters(
            self.cached_scan_result.discovered,
            self.include_tags,
            self.exclude_tags,
            self.min_rating,
        )

        # TODO: This should be simplified, since only the `matching_items` need to be added/updated in the cached scan result.
        return ScanResult(
            discovered=self.cached_scan_result.discovered,
            matching=matching_items,
            failed_count=self.cached_scan_result.failed_count,
            non_image_file_count=self.cached_scan_result.non_image_file_count,
        )

    def scan(self) -> ScanResult:
        """Scan the media directories for images and read their metadata, no filtering is applied."""
        results: list[ImageMeta] = []
        failed_count = 0
        non_image_file_count = 0

        for root in self.roots:
            root_path = Path(root)
            if not root_path.is_dir():
                _LOGGER.warning("Media root not found or not a directory: %s", root)
                continue

            # Count non-image files
            for p in root_path.rglob("*"):
                if p.is_file():
                    ext = p.suffix.lower()
                    if ext not in SUPPORTED_EXT:
                        non_image_file_count += 1

            for ext in SUPPORTED_EXT:
                for p in root_path.rglob(f"*{ext}"):
                    # Skip unreadable files (broken symlinks, permission issues)
                    if not p.is_file() or not os.access(p, os.R_OK):
                        failed_count += 1
                        continue

                    full = str(p)
                    try:
                        meta = self._read_metadata(full)
                        results.append(meta)
                    except Exception:
                        # On any error, still include the file with empty metadata
                        results.append(ImageMeta(path=full, tags=[], rating=0, date=None))
        return ScanResult(
            discovered=results,
            matching=None,
            failed_count=failed_count,
            non_image_file_count=non_image_file_count,
        )

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
