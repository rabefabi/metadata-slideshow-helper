from pathlib import Path

import pytest
from custom_components.metadata_slideshow_helper.scanner import MediaScanner, apply_filters


@pytest.mark.asyncio
async def test_filter_by_rating(test_images_multidir: tuple[list[Path], list[Path]]) -> None:
    """Test filtering images by minimum rating."""
    _, dir_paths = test_images_multidir
    assert len(dir_paths) > 1, "Should have multiple directories for testing"
    scanner = MediaScanner([str(d) for d in dir_paths])
    discovered_items = scanner.scan()

    # Filter for 4+ stars
    MIN_RATING = 4
    matching = apply_filters(discovered_items, [], [], min_rating=MIN_RATING)
    assert all(item.rating >= MIN_RATING for item in matching)
    assert any(item.rating > MIN_RATING for item in matching)  # Ensure higher ratings are included
    assert len(matching) < len(discovered_items)


@pytest.mark.asyncio
async def test_filter_by_tags(test_images_multidir: tuple[list[Path], list[Path]]) -> None:
    """Test filtering images by include/exclude tags."""
    _, dir_paths = test_images_multidir
    scanner = MediaScanner([str(d) for d in dir_paths])
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


@pytest.mark.asyncio
async def test_multiple_directories(test_images_multidir: tuple[list[Path], list[Path]]) -> None:
    """Test scanning multiple directories with split images.

    This test verifies that the scanner correctly combines images from
    multiple directories into a single result set, treating them as one
    logical collection.
    """
    num_expected_dirs = 2
    all_images, dir_paths = test_images_multidir

    # Verify we have the expected structure
    assert len(dir_paths) == num_expected_dirs, (
        f"Should have {num_expected_dirs} separate directories"
    )
    assert len(all_images) > 0, "Should have generated test images"

    # Scan each directory separately
    scanner_dir0 = MediaScanner([str(dir_paths[0])])
    items_dir0 = scanner_dir0.scan()

    scanner_dir1 = MediaScanner([str(dir_paths[1])])
    items_dir1 = scanner_dir1.scan()

    # Scan both directories together
    scanner_multi = MediaScanner([str(dir_paths[0]), str(dir_paths[1])])
    items_multi = scanner_multi.scan()

    # Verify that multi-directory scan combines results
    assert len(items_multi) == len(items_dir0) + len(items_dir1), (
        f"Multi-dir scan ({len(items_multi)}) should equal sum of individual scans ({len(items_dir0)} + {len(items_dir1)})"
    )

    # Verify that all images are found
    assert len(items_multi) == len(all_images), (
        f"Multi-dir scan found {len(items_multi)} images but expected {len(all_images)}"
    )

    # Verify filtering works across multiple directories
    matching = apply_filters(items_multi, include_tags=["vacation"], exclude_tags=[], min_rating=0)
    assert len(matching) > 0, "Should find vacation-tagged images across directories"

    # Verify that paths come from both directories
    paths_from_dir0 = [m.path for m in items_multi if dir_paths[0].name in m.path]
    paths_from_dir1 = [m.path for m in items_multi if dir_paths[1].name in m.path]

    assert len(paths_from_dir0) > 0, "Should have images from first directory"
    assert len(paths_from_dir1) > 0, "Should have images from second directory"
    assert len(paths_from_dir0) + len(paths_from_dir1) == len(items_multi), (
        "All images should originate from one of the two directories"
    )
