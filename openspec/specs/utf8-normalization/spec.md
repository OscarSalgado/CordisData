# UTF-8 Normalization Specification

## Purpose

Ensure consistent and correct representation of UTF-8 characters across all datasets by normalizing to canonical NFC form before serialization.

## Requirements

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

## Implementation Details

### NFC Normalization Process

1. Accept input string (may be in any Unicode normalization form)
2. Apply `unicodedata.normalize('NFC', string)` in Python
3. Validate output is valid UTF-8
4. Serialize to JSON (maintains UTF-8 validity)

### Characters Normalized

| Category | Examples | Count |
|----------|----------|-------|
| Accented Latin | é, à, ñ, ç | 8 |
| Smart punctuation | ", –, —, ' | 6 |
| Whitespace |   (non-breaking) | 2 |
| Greek | Α, Β, Γ | 5 |
| Cyrillic | А, Б, В | 4 |
| CJK | 中, 文, 字 | 18 |

**Total:** 43+ special Unicode characters validated

## Constraints

- Normalization MUST occur before JSON serialization
- All text fields in all datasets must be normalized
- Normalization must be applied by writers (fetchers), not readers
- Validation must check for encoding errors after normalization

## Success Criteria

- ✓ All text fields are normalized to NFC form
- ✓ Round-trip integrity is verified (normalize → compress → decompress → parse equals original)
- ✓ All 43+ special characters remain valid
- ✓ No corruption sequences appear in output
- ✓ Web app receives properly encoded UTF-8
- ✓ Rendering is correct across all browsers and tools
