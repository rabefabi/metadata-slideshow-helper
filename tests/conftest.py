from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from .image_generator import SAMPLE_MEDIA_DIR, TEST_IMAGE_SPECS, generate_test_images

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
def test_images(test_images_dir: Path) -> Generator[list[Path]]:
    """Generate test images with various metadata configurations.

    This fixture creates a comprehensive set of test images once per test session
    and ensures they're available for all tests. The images persist across test
    runs in a non-git-tracked directory.

    Yields:
        List of paths to generated test images

    Example:
        def test_scanner(test_images):
            scanner = MediaScanner(str(test_images[0].parent))
            results = scanner.scan()
            assert len(results) == len(test_images)
    """


    created_paths = generate_test_images(test_images_dir)
    yield created_paths
    # Images are intentionally not cleaned up to persist across test runs


# TODO: This fixture probably should return spec.rating >= rating, instead of ==
@pytest.fixture
def sample_image_by_rating(test_images_dir: Path, test_images: list[Path]):
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
            test_images_dir / spec.filename
            for spec in TEST_IMAGE_SPECS
            if spec.rating == rating
        ]

    return _get_by_rating


@pytest.fixture
def sample_image_by_tag(test_images_dir: Path, test_images: list[Path]):
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


        return [
            test_images_dir / spec.filename
            for spec in TEST_IMAGE_SPECS
            if tag in spec.tags
        ]

    return _get_by_tag
