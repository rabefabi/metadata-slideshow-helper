from pathlib import Path

import pytest
from custom_components.slideshow_helper.scanner import MediaScanner, apply_filters


@pytest.mark.asyncio
async def test_filter_by_rating(test_images: list[Path]) -> None:
    """Test filtering images by minimum rating."""
    scanner = MediaScanner(str(test_images[0].parent))
    all_items = scanner.scan()

    # Filter for 4+ stars
    filtered = apply_filters(all_items, [], [], min_rating=4)
    assert all(item.rating >= 4 for item in filtered)
    assert any(item.rating == 5 for item in filtered)
    assert len(filtered) < len(all_items)


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Tags are not yet implemented in test images")
async def test_filter_by_tags(test_images: list[Path]) -> None:
    """Test filtering images by include/exclude tags."""
    scanner = MediaScanner(str(test_images[0].parent))
    all_items = scanner.scan()

    # FIXME: Current implementation doesn't actually write tags to EXIF
    # This test demonstrates the API, but won't filter anything yet
    # as the scanner doesn't read tags from the image files

    # Include vacation tag
    tag_include = "vacation"
    tag_exclude = "private"
    filtered = apply_filters(
        all_items, include_tags=[tag_include], exclude_tags=[tag_exclude], min_rating=0
    )
    assert len(filtered) > 0
    for img in filtered:
        assert tag_include in img.tags
        assert tag_exclude not in img.tags
