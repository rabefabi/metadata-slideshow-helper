# 2025-12-23: Fix filtering in MediaScanner

Goals:

- Fix the filtering logic in `MediaScanner` to ensure it correctly filters media items based on tags and ratings

## Dev Diary

- Current implementation only considers ratings, not tags
- Tags are very inconsistent across platforms, tools and formats (EXIF, XMP, IPTC)
  - [ ] Considered all the differnt tag storage formats
    - XMP sidecar files
    - XMP embedded
    - ...?

## Photo Tagging Research Results

> Info: AI generated research results, statements & sources not yet verified.

- Approaches: Photographers store per-image tags/keywords, ratings, people, and status primarily in embedded XMP for JPEG/TIFF/PNG, XMP sidecar files (`.xmp`) for RAW formats (CR2/CR3, NEF, ARW), legacy IPTC IIM fields, limited EXIF user fields (e.g., Windows XP fields), and occasionally non-standard sidecars (e.g., Google Photos Takeout JSON, Picasa `.picasa.ini`). Catalog databases (Lightroom, Capture One, Apple Photos) often hold metadata internally unless explicitly written to XMP or exported.[^1][^2][^3][^4][^5][^6]
- Tags/Keywords: Modern, interoperable tags use XMP `dc:subject` (flat keywords) and optionally `lr:hierarchicalSubject` for hierarchical keyword trees; IPTC Core keywords map into XMP; legacy IPTC IIM `Keywords` may still exist and should be reconciled.[^2][^1][^7]
- Ratings: Common fields include `xmp:Rating` (0–5, some apps use `-1` as reject), EXIF `Exif.Image.Rating` and `RatingPercent`, and `MicrosoftPhoto:RatingPercent`. Prefer `xmp:Rating` and mirror to EXIF/Microsoft for Windows compatibility when writing.[^8][^7][^9]
- People/Face Regions: Names and regions are stored via MWG Regions (`mwg-rs`) with region `Type=Face`, optional Microsoft `MP:RegionInfo` for Windows, and IPTC Extension `Iptc4xmpExt:PersonInImage` for listing people names. Read both regions and names for best coverage.[^4][^10][^2]
- Flags/Status: Color labels use `xmp:Label`; pick/reject flags are not standardized across apps (some encode reject as `xmp:Rating=-1`). Treat labels and flags as app-specific unless a clear convention is configured.[^7][^4]
- Storage specifics: JPEG/TIFF/PNG can embed XMP alongside EXIF; PNG supports XMP chunks. RAW files typically use `.xmp` sidecars; writing directly into proprietary RAW is discouraged. When both embedded XMP and sidecars exist, use a precedence policy (e.g., newest-modified wins or sidecar prioritized).[^1][^4]
- Tool behaviors (typical): Lightroom/Bridge write embedded XMP for writable formats and `.xmp` sidecars for RAW when enabled; Darktable/digiKam commonly use sidecars (configurable); Windows Explorer reads EXIF `Rating/RatingPercent` and XP* fields; Apple Photos stores in a catalog and adds metadata mainly on export; Google Photos provides JSON sidecars via Takeout.[^11][^5][^12][^6]
- Practical scanner precedence: 1) `.xmp` sidecar if present; 2) embedded XMP; 3) IPTC Core/Extension (XMP); 4) IPTC IIM (legacy); 5) EXIF XP*and `Rating/RatingPercent`; 6) cloud-export sidecars (JSON/INI) as supplemental. De-duplicate across sources and normalize encodings (XP* are UCS-2).[^4][^8]

### Sources

- [^1]: Adobe XMP Specification: <https://developer.adobe.com/xmp/>
- [^2]: IPTC Photo Metadata Standard: <https://iptc.org/standards/photo-metadata/iptc-photo-metadata-standard/>
- [^3]: IPTC Core/Extension (XMP): <https://iptc.org/standards/photo-metadata/xmp/>
- [^4]: Metadata Working Group (MWG) Guidelines: <https://www.metadataworkinggroup.org/pdf/mwg_guidance.pdf> and overview: <https://exiftool.org/mwg.html>
- [^5]: Apple Photos export behavior: <https://support.apple.com/guide/photos/export-photos-videos-photosa6f2892/mac>
- [^6]: Google Photos Takeout (JSON sidecars): <https://support.google.com/accounts/answer/3024190>
- [^7]: ExifTool XMP Tag Reference: <https://exiftool.org/TagNames/XMP.html>
- [^8]: ExifTool EXIF Tag Reference (incl. Rating, XP*): <https://exiftool.org/TagNames/EXIF.html>
- [^9]: Exiv2 Tag Tables (RatingPercent, XP*): <https://exiv2.org/tags.html>
- [^10]: ExifTool Microsoft/RegionInfo: <https://exiftool.org/TagNames/Microsoft.html>
- [^11]: Adobe Bridge metadata & sidecars: <https://helpx.adobe.com/bridge/using/metadata-adobe-bridge.html>
- [^12]: Google Photos Help: <https://support.google.com/>

## Python Libraries for Photo Metadata

> Info: AI generated research results, statements & sources not yet verified.

### Overview

| Library | EXIF | IPTC | XMP | Sidecars | RAW | Thread Safe | External Deps | Best For | Repository |
|---------|------|------|-----|----------|-----|-------------|---------------|----------|------------|
| **Pillow** | ✅ R/W | ❌ | ✅ Read | ❌ | ❌ | ✅ | None | JPEG/PNG/TIFF embedded XMP, HA integrations | [python-pillow/Pillow](https://github.com/python-pillow/Pillow) |
| **exifread** | ✅ Read | ❌ | ❌ | ❌ | ⚠️ Limited | ✅ | None | Lightweight EXIF extraction | [ianare/exif-py](https://github.com/ianare/exif-py) |
| **piexif** | ✅ R/W | ❌ | ❌ | ❌ | ❌ | ✅ | None | EXIF manipulation, pure Python | [hMatoba/Piexif](https://github.com/hMatoba/Piexif) |
| **pyexiv2** | ✅ R/W | ✅ R/W | ✅ R/W | ⚠️ Manual | ✅ | ❌ | Exiv2 C++ | Full metadata, 60+ formats | [LeoHsiao1/pyexiv2](https://github.com/LeoHsiao1/pyexiv2) |
| **python-xmp-toolkit** | ❌ | ❌ | ✅ R/W | ✅ | ❌ | ⚠️ | libexempi | XMP sidecars, structured props | [python-xmp-toolkit/python-xmp-toolkit](https://github.com/python-xmp-toolkit/python-xmp-toolkit) |
| **exiftool** (subprocess) | ✅ R/W | ✅ R/W | ✅ R/W | ✅ | ✅ | ✅ | Perl binary | Comprehensive, RAW, gold standard | [exiftool/exiftool](https://github.com/exiftool/exiftool) |

> **Note for Home Assistant deployment**: Pillow is the recommended choice as it has no external dependencies and is already available in the HA environment. Other libraries require system-level packages (libexempi, Exiv2, Perl).

### Key Capabilities by Use Case

**Reading tags (`dc:subject`, `lr:hierarchicalSubject`)**:

- Pillow: ✅ Can read from embedded XMP via `getxmp()` (returns dict with XMP namespaces)
- pyexiv2: ✅ Full support (embedded + structured access)
- python-xmp-toolkit: ✅ Full XMP support (embedded + sidecars)
- exiftool: ✅ All formats (embedded + sidecars)
- Others: ❌ No XMP support

**Reading ratings (`xmp:Rating`, EXIF Rating)**:

- Pillow: ✅ Can read from embedded XMP and EXIF via `getexif()` and `getxmp()`
- pyexiv2: ✅ Both XMP and EXIF
- python-xmp-toolkit: ✅ XMP only
- exiftool: ✅ All fields
- piexif: ⚠️ EXIF only (limited)

**Reading people/faces (`mwg-rs`, `Iptc4xmpExt:PersonInImage`)**:

- Pillow: ⚠️ Can read from embedded XMP dict but requires manual parsing of nested structures
- pyexiv2: ✅ Full support with structured access
- python-xmp-toolkit: ✅ XMP structures
- exiftool: ✅ Complete

**XMP sidecar handling**:

- exiftool: ✅ Auto-reads, writes, syncs
- python-xmp-toolkit: ✅ Manual file handling
- pyexiv2: ⚠️ Must read `.xmp` as separate Image
- Pillow: ❌ No sidecar support
- Others: ❌ No support

### Implementation Notes

- **Pillow for HA integration**: For this project (Home Assistant integration), Pillow is sufficient for reading embedded XMP from JPEG/TIFF/PNG files. It's thread-safe, has no external dependencies, and supports the primary use case of filtering by tags and ratings from embedded metadata.
- **Sidecar support**: If XMP sidecar support is needed in the future, consider exiftool via subprocess as a fallback (though this requires Perl to be available in the HA container).
- **Format support**: For RAW formats (CR2, NEF, ARW), XMP sidecars are the standard approach, but most HA users will likely work with JPEG/PNG files from their photo libraries.[^1][^4]
- **XMP parsing**: Pillow's `getxmp()` returns a dictionary with XMP data. Keys follow XMP namespace conventions (e.g., `dc:subject` for tags, `xmp:Rating` for ratings).

## Implementation Decision

**Chosen approach**: Pillow + defusedxml for embedded XMP reading

**Rationale**:

1. **HA compatibility**: Pillow is already available in Home Assistant; defusedxml is pure Python with no system dependencies
2. **YAGNI principle**: No fallback to raw byte parsing—Pillow with defusedxml handles all our test cases
3. **Thread-safe**: Safe for concurrent use in HA event loop
4. **Sufficient coverage**: Reads embedded XMP from JPEG/PNG (the common formats in photo libraries)

**Technical details**:

- Pillow's `getxmp()` requires defusedxml to parse XMP; returns nested dict: `{'xmpmeta': {'RDF': {'Description': {...}}}}`
- Tags extracted from: `Description.subject.Bag.li` (string or list)
- Rating extracted from: `Description.Rating` (string converted to int)
- Also reads EXIF rating via piexif for JPEG files as fallback

**Trade-offs**:

- ✅ No external binary dependencies (Perl, libexempi, Exiv2)
- ✅ Works with embedded XMP in JPEG/PNG
- ❌ No XMP sidecar support (not needed for initial use case)
- ❌ No RAW format support (users expected to have JPEG exports)

**Dependencies added**:

- `defusedxml>=0.7` added to test extras in pyproject.toml

**Files modified**:

- `custom_components/slideshow_helper/scanner.py`: Parse Pillow's XMP dict format
- `tests/image_generator.py`: Embed XMP packets in test images (JPEG APP1, PNG iTXt)
- `pyproject.toml`: Added defusedxml test dependency
