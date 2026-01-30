from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from .image_generator import (
    SAMPLE_MEDIA_DIR,
    TEST_IMAGE_SPECS,
    generate_test_images_across_dirs,
)

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session")
def test_images_dir() -> Path:
    """Return the directory path for test images.

    This directory persists across test runs and is not tracked by git.
    Uses sample-media which is mounted into the Home Assistant dev container.
    """
    test_dir = SAMPLE_MEDIA_DIR
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture(scope="session")
def test_images_multidir(test_images_dir: Path) -> Generator[tuple[list[Path], list[Path]]]:
    """Generate test images split across multiple subdirectories.

    This fixture creates images in separate directories within SAMPLE_MEDIA_DIR
    to test multi-directory scanning functionality. The images are distributed
    evenly across directories.

    Yields:
        Tuple of (list of all image paths, list of directory paths)
    """
    # Create subdirectories within the main test images directory
    multi_dir_parent = test_images_dir / "by_year"
    created_paths, dir_paths = generate_test_images_across_dirs(
        multi_dir_parent, num_dirs=2, specs=TEST_IMAGE_SPECS
    )
    yield created_paths, dir_paths
    # Images are intentionally not cleaned up to persist across test runs


@pytest.fixture
def sample_image_by_rating(
    test_images_dir: Path, test_images_multidir: tuple[list[Path], list[Path]]
):
    """Provide a helper to get test images filtered by rating.

    Args:
        test_images_dir: Directory containing test images
        test_images: Ensure images are generated

    Returns:
        Callable that returns list of image paths matching the given rating

    Example:
        def test_rating_filter(sample_image_by_rating):
            five_star_images = sample_image_by_rating(5)
            assert all(img.rating == 5 for img in five_star_images)
    """

    def _get_by_rating(rating: int) -> list[Path]:
        return [
            test_images_dir / spec.filename for spec in TEST_IMAGE_SPECS if spec.rating == rating
        ]

    return _get_by_rating


@pytest.fixture
def sample_image_by_tag(test_images_dir: Path, test_images_multidir: tuple[list[Path], list[Path]]):
    """Provide a helper to get test images filtered by tag.

    Args:
        test_images_dir: Directory containing test images
        test_images: Ensure images are generated

    Returns:
        Callable that returns list of image paths containing the given tag

    Example:
        def test_tag_filter(sample_image_by_tag):
            vacation_images = sample_image_by_tag("vacation")
            assert all("vacation" in img.name for img in vacation_images)
    """

    def _get_by_tag(tag: str) -> list[Path]:
        return [test_images_dir / spec.filename for spec in TEST_IMAGE_SPECS if tag in spec.tags]

    return _get_by_tag
