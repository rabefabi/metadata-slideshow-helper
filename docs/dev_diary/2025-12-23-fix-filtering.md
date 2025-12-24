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
