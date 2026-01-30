from pathlib import Path

import pytest
from custom_components.metadata_slideshow_helper.scanner import MediaScanner, apply_filters


@pytest.mark.asyncio
async def test_filter_by_rating(test_images: list[Path]) -> None:
    """Test filtering images by minimum rating."""
    scanner = MediaScanner(str(test_images[0].parent))
    discovered_items = scanner.scan()

    # Filter for 4+ stars
    MIN_RATING = 4
    matching = apply_filters(discovered_items, [], [], min_rating=MIN_RATING)
    assert all(item.rating >= MIN_RATING for item in matching)
    assert any(item.rating > MIN_RATING for item in matching)  # Ensure higher ratings are included
    assert len(matching) < len(discovered_items)


@pytest.mark.asyncio
async def test_filter_by_tags(test_images: list[Path]) -> None:
    """Test filtering images by include/exclude tags."""
    scanner = MediaScanner(str(test_images[0].parent))
    discovered_items = scanner.scan()

    # Include vacation tag
    tag_include = ["vacation", "family"]
    tag_exclude = ["private", "exclude"]
    matching = apply_filters(
        discovered_items, include_tags=tag_include, exclude_tags=tag_exclude, min_rating=0
    )
    assert len(matching) > 0
    for img in matching:
        assert all(tag in img.tags for tag in tag_include)
        assert all(tag not in img.tags for tag in tag_exclude)
