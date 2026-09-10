# Artwork

Luna can audit missing or invalid embedded album artwork and build reviewable replacement plans.

## Format-aware inspection

Artwork inspection uses format-specific handling for supported containers, including:

- MP3 ID3 `APIC` artwork
- M4A/MP4 `covr` artwork
- FLAC picture blocks

When Pillow is available, Luna can report artwork MIME type and dimensions and distinguish missing artwork from invalid artwork payloads. An artwork entry can exist while its image payload is empty or otherwise invalid; Luna reports that as invalid rather than treating it as a valid cover.

## Local candidates

Recognized local candidates include:

- `cover.jpg`
- `folder.jpg`
- `front.png`
- `albumart.jpg`

Artwork replacement requires an explicit reviewed plan and approval before applying. If no safe candidate exists, the artwork plan reports `candidate: null` rather than inventing a replacement.
