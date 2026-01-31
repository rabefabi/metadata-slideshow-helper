"""Verify test fixtures for image generation and filtering."""

from pathlib import Path

import pytest
from custom_components.metadata_slideshow_helper.scanner import MediaScanner


def test_sample_image_by_rating_fixture(sample_image_by_rating) -> None:
    """Verify the rating filter fixture works correctly."""
    five_star = sample_image_by_rating(5)
    assert len(five_star) > 0

    zero_star = sample_image_by_rating(0)
    assert len(zero_star) > 0

    # Verify filenames contain rating indicator
    for img in five_star:
        assert "rating_5" in img.name and "rating_0" not in img.name


def test_sample_image_by_tag_fixture(sample_image_by_tag) -> None:
    """Verify the tag filter fixture works correctly."""
    vacation = sample_image_by_tag("vacation")
    assert len(vacation) > 0

    family = sample_image_by_tag("family")
    assert len(family) > 0

    # Verify filenames indicate the tag
    for img in vacation:
        assert "vacation" in img.name


@pytest.mark.asyncio
async def test_media_scanner_with_test_images(
    test_images_multidir: tuple[list[Path], list[Path]],
) -> None:
    """Integration test using the scanner with generated test images."""
    # Images are organized in subdirectories (by_year/dir_0, by_year/dir_1)
    # Scan both directories to get all images
    all_images, dir_paths = test_images_multidir
    scanner = MediaScanner([str(d) for d in dir_paths])
    scan_result = scanner.scan()

    # Should find all the generated images
    assert len(scan_result.discovered) == len(all_images)

    # Check that ratings were properly read
    ratings = [r.rating for r in scan_result.discovered]
    assert max(ratings) == 5  # noqa: PLR2004 magic number is accepted here
    assert min(ratings) == 0
