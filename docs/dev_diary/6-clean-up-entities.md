# Dev Diary Issue 6: Clean Up Entities

See <https://github.com/rabefabi/metadata-slideshow-helper/issues/6>

## Better Naming for Entity Attributes

Conducted a comprehensive terminology review across the entire codebase to identify and resolve naming ambiguities. The most significant issues were: "image" being used for both raw and filtered results, "refresh" conflating filesystem rescans with coordinator updates, and "cycle" being technical jargon. Renamed all instances to use clearer terms, see the terminology table to the README documenting the four key concepts: discovered images, matching images, rescan, and advance.
