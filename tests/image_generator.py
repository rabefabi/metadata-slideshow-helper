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
from PIL.PngImagePlugin import PngInfo

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

    # Build XMP packet for tags/ratings
    xmp_bytes = _build_xmp_packet(spec.tags, spec.rating)

    # Save the image (PNG can embed XMP via iTXt)
    if output_path.suffix.lower() == ".png":
        pnginfo = PngInfo()
        pnginfo.add_itxt("XML:com.adobe.xmp", xmp_bytes.decode("utf-8"))
        img.save(output_path, quality=95, pnginfo=pnginfo)
    else:
        img.save(output_path, quality=95)

    # Add EXIF metadata and XMP (for JPEG files only)
    if output_path.suffix.lower() in {".jpg", ".jpeg"}:
        try:
            exif_dict: dict[str, dict | None] = {
                "0th": {},
                "Exif": {},
                "GPS": {},
                "1st": {},
                "thumbnail": None,
            }

            # Set rating in EXIF (mirrors xmp:Rating for compatibility)
            if spec.rating > 0:
                exif_dict["0th"][piexif.ImageIFD.Rating] = spec.rating  # type: ignore

            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, str(output_path))

            _embed_xmp_jpeg(output_path, xmp_bytes)

            _LOGGER.info(
                "Created test image: %s (rating=%d, tags=%s)",
                output_path.name,
                spec.rating,
                spec.tags,
            )
        except Exception as e:
            _LOGGER.error("Failed to write EXIF/XMP metadata for %s: %s", output_path.name, e)


def create_broken_image(output_path: Path) -> None:
    """Create a broken image file by creating a symlink to a non-existent file.

    This simulates files that can't be read (e.g., deleted source, broken symlinks).

    Args:
        output_path: Path where the broken symlink will be created
    """
    # Create a symlink to a non-existent file
    non_existent = output_path.parent / f"nonexistent_{output_path.stem}"
    output_path.symlink_to(non_existent)
    _LOGGER.info("Created broken image symlink: %s", output_path.name)


def create_non_image_file(output_path: Path, content: str = "test content") -> None:
    """Create a non-image file in the media directory.

    Args:
        output_path: Path where the non-image file will be created
        content: Text content for the file
    """
    output_path.write_text(content)
    _LOGGER.info("Created non-image file: %s", output_path.name)


def generate_test_images(
    output_dir: Path,
    specs: Sequence[TestImageSpec] = TEST_IMAGE_SPECS,
    include_broken_images: bool = False,
    include_non_image_files: bool = False,
) -> list[Path]:
    """Generate a complete set of test images.

    Args:
        output_dir: Directory where test images will be created
        specs: Optional list of image specs; uses TEST_IMAGE_SPECS if not provided
        include_broken_images: If True, also create some corrupted image files
        include_non_image_files: If True, also create non-image files (.txt, .pdf, etc.)

    Returns:
        List of paths to created images
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    created_paths = []
    for spec in specs:
        output_path = output_dir / spec.filename
        create_test_image(spec, output_path)
        created_paths.append(output_path)

    # Optionally create broken images
    if include_broken_images:
        for i in range(2):
            broken_path = output_dir / f"broken_image_{i}.jpg"
            create_broken_image(broken_path)

    # Optionally create non-image files
    if include_non_image_files:
        non_image_files = [
            ("readme.txt", "This is a readme file"),
            ("config.json", '{"setting": "value"}'),
            ("notes.md", "# Notes\n\nSome notes about the images"),
            ("data.csv", "id,name,value\n1,test,123"),
        ]
        for filename, content in non_image_files:
            non_image_path = output_dir / filename
            create_non_image_file(non_image_path, content)

    _LOGGER.info("Generated %d test images in %s", len(created_paths), output_dir)
    return created_paths


def generate_test_images_across_dirs(
    parent_dir: Path,
    num_dirs: int = 2,
    specs: Sequence[TestImageSpec] = TEST_IMAGE_SPECS,
    include_broken_images: bool = False,
    include_non_image_files: bool = False,
) -> tuple[list[Path], list[Path]]:
    """Generate test images split across multiple subdirectories.

    Args:
        parent_dir: Parent directory under which subdirectories will be created
        num_dirs: Number of subdirectories to create
        specs: Image specifications to distribute across directories
        include_broken_images: If True, also create some corrupted image files
        include_non_image_files: If True, also create non-image files

    Returns:
        Tuple of (list of all created image paths, list of directory paths)
    """
    parent_dir.mkdir(parents=True, exist_ok=True)

    all_images = []
    dir_paths = []

    # Split specs evenly across directories
    specs_per_dir = len(specs) // num_dirs

    for dir_idx in range(num_dirs):
        dir_path = parent_dir / f"dir_{dir_idx}"
        dir_path.mkdir(parents=True, exist_ok=True)
        dir_paths.append(dir_path)

        # Get specs for this directory
        start_idx = dir_idx * specs_per_dir
        end_idx = start_idx + specs_per_dir if dir_idx < num_dirs - 1 else len(specs)
        dir_specs = specs[start_idx:end_idx]

        # Generate images in this directory
        for spec in dir_specs:
            output_path = dir_path / spec.filename
            create_test_image(spec, output_path)
            all_images.append(output_path)

        # Optionally create broken images in each directory
        if include_broken_images:
            broken_path = dir_path / f"broken_image_{dir_idx}.jpg"
            create_broken_image(broken_path)

        # Optionally create non-image files in each directory
        if include_non_image_files:
            non_image_path = dir_path / f"notes_{dir_idx}.txt"
            create_non_image_file(non_image_path, f"Notes for directory {dir_idx}")

    _LOGGER.info(
        "Generated %d test images across %d directories in %s",
        len(all_images),
        num_dirs,
        parent_dir,
    )
    return all_images, dir_paths


def cleanup_test_images(output_dir: Path) -> None:
    """Remove all test images from the output directory and subdirectories.

    Args:
        output_dir: Directory containing test images to clean up
    """
    if not output_dir.exists():
        return

    count = 0
    # Clean up files in subdirectories
    for subdir in output_dir.glob("dir_*"):
        if subdir.is_dir():
            for file_path in subdir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    count += 1

    # Clean up files in root
    for file_path in output_dir.glob("*"):
        if file_path.is_file():
            file_path.unlink()
            count += 1

    _LOGGER.info("Cleaned up %d test images from %s", count, output_dir)


def _build_xmp_packet(tags: list[str], rating: int) -> bytes:
    """Build a minimal XMP packet containing tags and rating.

    The packet uses dc:subject for keywords and xmp:Rating for stars, which Pillow can read
    via getxmp() in tests.
    """

    # Build <rdf:Bag> of dc:subject entries
    bag_items = "".join(f"<rdf:li>{tag}</rdf:li>" for tag in tags)
    dc_subject = f"<dc:subject><rdf:Bag>{bag_items}</rdf:Bag></dc:subject>" if tags else ""

    rating_str = f"<xmp:Rating>{rating}</xmp:Rating>" if rating else ""

    description = f'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:xmp="http://ns.adobe.com/xap/1.0/">{dc_subject}{rating_str}</rdf:Description>'

    xmp = (
        '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        f"{description}"
        "</rdf:RDF>"
        "</x:xmpmeta>"
        '<?xpacket end="w"?>'
    )

    return xmp.encode("utf-8")


def _embed_xmp_jpeg(path: Path, xmp_bytes: bytes) -> None:
    """Embed XMP packet into a JPEG as an APP1 segment after SOI.

    This avoids extra dependencies and keeps tests self-contained.
    """

    data = path.read_bytes()
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("Not a JPEG file")

    xmp_header = b"http://ns.adobe.com/xap/1.0/\x00"
    app1_payload = xmp_header + xmp_bytes
    app1_length = len(app1_payload) + 2  # includes length bytes themselves
    app1 = b"\xff\xe1" + app1_length.to_bytes(2, "big") + app1_payload

    new_data = b"\xff\xd8" + app1 + data[2:]
    path.write_bytes(new_data)


if __name__ == "__main__":
    # Allow running this script directly to generate images
    logging.basicConfig(level=logging.INFO)
    generate_test_images(
        SAMPLE_MEDIA_DIR,
        include_broken_images=True,
        include_non_image_files=True,
    )
    print(f"Generated test images in {SAMPLE_MEDIA_DIR}")

    # Also generate multi-directory setup with diagnostics
    multi_dir = SAMPLE_MEDIA_DIR / "multi_dir_test"
    images, dirs = generate_test_images_across_dirs(
        multi_dir,
        num_dirs=2,
        include_broken_images=True,
        include_non_image_files=True,
    )
    print(
        f"Generated {len(images)} test images across {len(dirs)} directories "
        f"with broken images and non-image files in {multi_dir}"
    )
