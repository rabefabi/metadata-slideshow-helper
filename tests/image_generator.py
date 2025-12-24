"""Helper script to generate test images with various metadata configurations.

This module creates test images with different ratings and tags for testing
the slideshow helper's filtering and selection logic.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import piexif
from PIL import Image, ImageDraw, ImageFont

_LOGGER = logging.getLogger(__name__)

# Single source of truth for the sample media directory used in tests
SAMPLE_MEDIA_DIR = Path(__file__).parent.parent / "sample-media"


@dataclass
class TestImageSpec:
    """Metadata Specification for a test image."""

    filename: str
    rating: int
    tags: list[str]
    color: tuple[int, int, int]

    @property
    def text(self) -> str:
        """Auto-generate text from rating and tags."""
        tags_str = ", ".join(self.tags) if self.tags else "(none)"
        return f"{self.filename}\nRating: {self.rating}\nTags: {tags_str}"


# Predefined test image specifications
TEST_IMAGE_SPECS: tuple[TestImageSpec, ...] = (
    # No rating, no tags
    TestImageSpec("simple_norating_notags.jpg", 0, [], (255, 100, 100)),
    # Various ratings, no tags
    TestImageSpec("rating_1_notags.jpg", 1, [], (200, 200, 255)),
    TestImageSpec("rating_3_notags.jpg", 3, [], (100, 255, 100)),
    TestImageSpec("rating_5_notags.jpg", 5, [], (255, 215, 0)),
    # Rating with single tags
    TestImageSpec("rating_4_vacation.jpg", 4, ["vacation"], (255, 150, 150)),
    TestImageSpec("rating_5_family.jpg", 5, ["family"], (150, 255, 150)),
    TestImageSpec("rating_2_work.jpg", 2, ["work"], (150, 150, 255)),
    # Multiple tags
    TestImageSpec(
        "rating_5_vacation_family.jpg",
        5,
        ["vacation", "family"],
        (255, 200, 150),
    ),
    TestImageSpec(
        "rating_3_vacation_beach.jpg",
        3,
        ["vacation", "beach"],
        (100, 200, 255),
    ),
    # Edge cases
    TestImageSpec("rating_0_exclude.jpg", 0, ["exclude"], (128, 128, 128)),
    TestImageSpec("rating_4_private.jpg", 4, ["private"], (200, 100, 200)),
    TestImageSpec("rating_3_draft.jpg", 3, ["draft"], (180, 180, 100)),
    # Multi-tag combinations for complex filtering
    TestImageSpec(
        "rating_5_vacation_private.jpg",
        5,
        ["vacation", "private"],
        (255, 100, 255),
    ),
    TestImageSpec(
        "rating_4_family_exclude.jpg",
        4,
        ["family", "exclude"],
        (100, 100, 100),
    ),
    # PNG files for format testing
    TestImageSpec("rating_3_png.png", 3, ["test"], (200, 150, 200)),
    TestImageSpec("rating_5_png.png", 5, ["test", "png"], (150, 200, 200)),
)


def create_test_image(spec: TestImageSpec, output_path: Path) -> None:
    """Create a single test image with the specified metadata.

    Args:
        spec: Image specification with rating, tags, and visual properties
        output_path: Full path where the image should be saved
    """
    # Create image with solid color background
    img = Image.new("RGB", (800, 600), color=spec.color)

    # Add text overlay
    if spec.text:
        draw = ImageDraw.Draw(img)

        font = ImageFont.load_default()

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), spec.text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (800 - text_width) // 2
        y = (600 - text_height) // 2

        # Draw text with shadow for better visibility
        draw.text((x + 2, y + 2), spec.text, fill=(0, 0, 0), font=font)
        draw.text((x, y), spec.text, fill=(255, 255, 255), font=font)

    # Save the image
    img.save(output_path, quality=95)

    # Add EXIF metadata (for JPEG files only)
    if output_path.suffix.lower() in {".jpg", ".jpeg"}:
        try:
            # Create EXIF data with rating
            exif_dict: dict[str, dict|None] = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

            # Set rating in EXIF
            if spec.rating > 0:
                exif_dict["0th"][piexif.ImageIFD.Rating] = spec.rating # type: ignore

            # Convert and insert EXIF data
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, str(output_path))

            _LOGGER.info(
                "Created test image: %s (rating=%d, tags=%s)",
                output_path.name,
                spec.rating,
                spec.tags,
            )
        except Exception as e:
            _LOGGER.error("Failed to write EXIF metadata for %s: %s", output_path.name, e)


def generate_test_images(
    output_dir: Path, specs: Sequence[TestImageSpec] = TEST_IMAGE_SPECS
) -> list[Path]:
    """Generate a complete set of test images.

    Args:
        output_dir: Directory where test images will be created
        specs: Optional list of image specs; uses TEST_IMAGE_SPECS if not provided

    Returns:
        List of paths to created images
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    created_paths = []
    for spec in specs:
        output_path = output_dir / spec.filename
        create_test_image(spec, output_path)
        created_paths.append(output_path)

    _LOGGER.info("Generated %d test images in %s", len(created_paths), output_dir)
    return created_paths


def cleanup_test_images(output_dir: Path) -> None:
    """Remove all test images from the output directory.

    Args:
        output_dir: Directory containing test images to clean up
    """
    if not output_dir.exists():
        return

    count = 0
    for file_path in output_dir.glob("*"):
        if file_path.is_file() and file_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            file_path.unlink()
            count += 1

    _LOGGER.info("Cleaned up %d test images from %s", count, output_dir)


if __name__ == "__main__":
    # Allow running this script directly to generate images
    logging.basicConfig(level=logging.INFO)
    generate_test_images(SAMPLE_MEDIA_DIR)
    print(f"Generated {len(TEST_IMAGE_SPECS)} test images in {SAMPLE_MEDIA_DIR}")
