## ADDED Requirements

### Requirement: Normalize UTF-8 to canonical NFC form
The system SHALL normalize all UTF-8 strings to NFC (Normalization Form Canonical Composition) to ensure consistent representation of characters and prevent rendering issues across different platforms and tools.

#### Scenario: Normalize accented characters
- **WHEN** data contains characters like é, à, ñ with combining diacritics
- **THEN** system converts to canonical form (é as single character U+00E9 instead of e + combining accent)
- **AND** visual representation remains identical but bytes are canonical

#### Scenario: Normalize special punctuation
- **WHEN** data contains smart quotes ("), en-dashes (–), non-breaking spaces (\xa0)
- **THEN** system normalizes to canonical UTF-8 representation
- **AND** prevents corruption sequences like "M-bM-^@M-^Y" when viewed in ASCII-limited tools

#### Scenario: Preserve multilingual content
- **WHEN** data contains characters from multiple languages (Latin, Greek, Cyrillic, CJK, etc.)
- **THEN** normalization preserves semantic meaning and character identity
- **AND** all 43+ special Unicode characters in dataset remain valid

### Requirement: Validate UTF-8 integrity
The system SHALL validate that all strings remain valid UTF-8 after normalization, with no data loss or corruption.

#### Scenario: Verify round-trip integrity
- **WHEN** data is normalized and written to JSONL
- **THEN** decompression and parsing produces identical records
- **AND** no characters are lost or corrupted in the process
- **AND** web app receives properly formed UTF-8 that renders correctly across browsers
