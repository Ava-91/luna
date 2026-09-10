# Metadata

Luna checks and normalizes common music metadata:

- Title
- Artist
- Album
- Album artist
- Track/disc information
- Year and genre
- Missing, placeholder, malformed, and parser-error conditions

Metadata changes are planned first and applied only with explicit confirmation.

## Empty values

Whitespace-only and other configured placeholder values are treated as missing during normalization. A planned `None` value means **clear the tag**, not write the literal string `"None"`.

For example, a whitespace-only album value can be normalized to `None`, applied, and then verified by running inspection/normalization again. Once the tag is genuinely absent, the normalization plan contains no repeated change.

## Safety

Metadata writes are explicit operations and can be recorded in the operation log for rollback. Missing metadata is reported rather than guessed or silently invented.
