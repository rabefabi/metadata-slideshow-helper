from pathlib import Path

import pytest
from custom_components.metadata_slideshow_helper.scanner import MediaScanner, apply_filters

from tests.image_generator import (
    generate_test_images,
    generate_test_images_across_dirs,
)


@pytest.mark.asyncio
async def test_filter_by_rating(test_images_multidir: tuple[list[Path], list[Path]]) -> None:
    """Test filtering images by minimum rating."""
    _, dir_paths = test_images_multidir
    assert len(dir_paths) > 1, "Should have multiple directories for testing"
    scanner = MediaScanner([str(d) for d in dir_paths])
    scan_result = scanner.scan()

    # Filter for 4+ stars
    MIN_RATING = 4
    matching = apply_filters(scan_result.discovered, [], [], min_rating=MIN_RATING)
    assert all(item.rating >= MIN_RATING for item in matching)
    assert any(item.rating > MIN_RATING for item in matching)  # Ensure higher ratings are included
    assert len(matching) < len(scan_result.discovered)


@pytest.mark.asyncio
async def test_filter_by_tags(test_images_multidir: tuple[list[Path], list[Path]]) -> None:
    """Test filtering images by include/exclude tags."""
    _, dir_paths = test_images_multidir
    scanner = MediaScanner([str(d) for d in dir_paths])
    scan_result = scanner.scan()

    # Include vacation tag
    tag_include = ["vacation", "family"]
    tag_exclude = ["private", "exclude"]
    matching = apply_filters(
        scan_result.discovered, include_tags=tag_include, exclude_tags=tag_exclude, min_rating=0
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
    result_dir0 = scanner_dir0.scan()

    scanner_dir1 = MediaScanner([str(dir_paths[1])])
    result_dir1 = scanner_dir1.scan()

    # Scan both directories together
    scanner_multi = MediaScanner([str(dir_paths[0]), str(dir_paths[1])])
    result_multi = scanner_multi.scan()

    # Verify that multi-directory scan combines results
    assert len(result_multi.discovered) == len(result_dir0.discovered) + len(
        result_dir1.discovered
    ), (
        f"Multi-dir scan ({len(result_multi.discovered)}) should equal sum of individual scans ({len(result_dir0.discovered)} + {len(result_dir1.discovered)})"
    )

    # Verify that all images are found
    assert len(result_multi.discovered) == len(all_images), (
        f"Multi-dir scan found {len(result_multi.discovered)} images but expected {len(all_images)}"
    )

    # Verify filtering works across multiple directories
    matching = apply_filters(
        result_multi.discovered, include_tags=["vacation"], exclude_tags=[], min_rating=0
    )
    assert len(matching) > 0, "Should find vacation-tagged images across directories"

    # Verify that paths come from both directories
    paths_from_dir0 = [m.path for m in result_multi.discovered if dir_paths[0].name in m.path]
    paths_from_dir1 = [m.path for m in result_multi.discovered if dir_paths[1].name in m.path]

    assert len(paths_from_dir0) > 0, "Should have images from first directory"
    assert len(paths_from_dir1) > 0, "Should have images from second directory"
    assert len(paths_from_dir0) + len(paths_from_dir1) == len(result_multi.discovered), (
        "All images should originate from one of the two directories"
    )


@pytest.mark.asyncio
async def test_diagnostic_metrics_with_broken_and_non_images(tmp_path: Path) -> None:
    """Test that failed and non-image file diagnostics are properly tracked.

    This test verifies the diagnostic metrics:
    - failed_count: tracks unreadable image files
    - non_image_file_count: tracks non-image files in the directory
    """
    # Generate test images with broken images and non-image files
    test_dir = tmp_path / "diagnostic_test"
    generate_test_images(
        test_dir,
        include_broken_images=True,
        include_non_image_files=True,
    )

    # Scan the directory
    scanner = MediaScanner([str(test_dir)])
    scan_result = scanner.scan()

    # Verify we found valid images
    assert len(scan_result.discovered) > 0, "Should have found some valid images"

    # Verify broken images were detected
    assert scan_result.failed_count > 0, "Should have detected broken/failed images"

    # Verify non-image files were counted
    assert scan_result.non_image_file_count > 0, "Should have counted non-image files"

    # Verify the metrics make sense together
    # Total files = valid images + failed images + non-image files
    # Note: Using scandir to count both regular files and symlinks
    files_on_disk = list(test_dir.iterdir())
    assert len(
        scan_result.discovered
    ) + scan_result.failed_count + scan_result.non_image_file_count == len(files_on_disk), (
        f"Total of metrics should equal total files on disk: {len(scan_result.discovered)} + {scan_result.failed_count} + {scan_result.non_image_file_count} != {len(files_on_disk)}"
    )


@pytest.mark.asyncio
async def test_diagnostic_metrics_across_directories(tmp_path: Path) -> None:
    """Test diagnostic metrics when scanning multiple directories.

    Verifies that failed and non-image file counts are aggregated correctly
    across multiple directories.
    """
    # Generate test images across multiple directories with diagnostics
    test_dir = tmp_path / "multi_diagnostic"
    _, dir_paths = generate_test_images_across_dirs(
        test_dir,
        num_dirs=2,
        include_broken_images=True,
        include_non_image_files=True,
    )

    # Scan each directory separately
    scanner_dir0 = MediaScanner([str(dir_paths[0])])
    result_dir0 = scanner_dir0.scan()

    scanner_dir1 = MediaScanner([str(dir_paths[1])])
    result_dir1 = scanner_dir1.scan()

    # Scan both directories together
    scanner_multi = MediaScanner([str(dir_paths[0]), str(dir_paths[1])])
    result_multi = scanner_multi.scan()

    # Verify metrics are aggregated correctly
    assert result_multi.failed_count == result_dir0.failed_count + result_dir1.failed_count, (
        f"Failed count should be aggregated: {result_multi.failed_count} != {result_dir0.failed_count} + {result_dir1.failed_count}"
    )
    assert (
        result_multi.non_image_file_count
        == result_dir0.non_image_file_count + result_dir1.non_image_file_count
    ), (
        f"Non-image count should be aggregated: {result_multi.non_image_file_count} != {result_dir0.non_image_file_count} + {result_dir1.non_image_file_count}"
    )

    # Verify each directory has at least one failed image and non-image file
    assert result_dir0.failed_count > 0 and result_dir0.non_image_file_count > 0, (
        "Dir 0 should have diagnostics"
    )
    assert result_dir1.failed_count > 0 and result_dir1.non_image_file_count > 0, (
        "Dir 1 should have diagnostics"
    )


@pytest.mark.asyncio
async def test_diagnostic_metrics_caching(tmp_path: Path) -> None:
    """Test that diagnostic metrics are properly cached and don't reset to zero.

    This is a regression test for a bug where failed_count and non_image_file_count
    would reset to 0 when scan_and_filter() used cached results instead of re-scanning.
    """
    # Generate test images with diagnostics
    test_dir = tmp_path / "cache_test"
    generate_test_images(
        test_dir,
        include_broken_images=True,
        include_non_image_files=True,
    )

    # Create scanner with a long rescan interval to ensure caching behavior
    scanner = MediaScanner([str(test_dir)], rescan_interval=3600)

    # First call - triggers actual scan
    result1 = scanner.scan_and_filter()
    assert result1.failed_count > 0, "Should have failed images on first scan"
    assert result1.non_image_file_count > 0, "Should have non-image files on first scan"

    # Store the initial counts
    initial_failed = result1.failed_count
    initial_non_image = result1.non_image_file_count

    # Second call - should use cached results
    result2 = scanner.scan_and_filter()

    # Verify diagnostic metrics are preserved from cache
    assert result2.failed_count == initial_failed, (
        f"Failed count should be cached: {result2.failed_count} != {initial_failed}"
    )
    assert result2.non_image_file_count == initial_non_image, (
        f"Non-image count should be cached: {result2.non_image_file_count} != {initial_non_image}"
    )

    # Verify discovered and matching counts are also consistent
    assert len(result2.discovered) == len(result1.discovered), "Discovered count should match"
    assert len(result2.matching) == len(result1.matching), "Matching count should match"
