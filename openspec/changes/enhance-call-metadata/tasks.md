## 1. HTML Cleaning Infrastructure

- [x] 1.1 Create `src/cordis_data/data/html_clean.py` with `clean_html_to_text()` function
- [x] 1.2 Implement plaintext extraction (unescape entities, strip tags, preserve spacing)
- [x] 1.3 Write unit tests for HTML cleaning (handle edge cases: empty, null, entities, nested tags)

## 2. Field Extraction in CallsFetcher

- [x] 2.1 Update `CallsFetcher._transform_record()` to extract `description` from `metadata.descriptionByte`
- [x] 2.2 Extract `objectives` (concat `destinationDescription` + `destinationDetails`)
- [x] 2.3 Extract `submissionProcedure` parsed from `metadata.actions[0]` (JSON)
- [x] 2.4 Extract `callTitle`, `deadlineModel`, `crossCuttingPriorities`, `typesOfAction`
- [x] 2.5 Extract `topicConditions` and `supportInfo` (clean HTML)
- [x] 2.6 Add 3 convenience URLs: `qnaUrl`, `updatesUrl`, `documentsUrl`

## 3. Field Validation and Type Safety

- [x] 3.1 Add type hints for new fields in call record dict
- [x] 3.2 Run pyright to verify type coverage
- [x] 3.3 Ensure all new fields have sensible defaults (empty string, None, empty list)

## 4. Unit Tests for Field Extraction

- [x] 4.1 Test extraction of each of 9 new fields with real API response structure
- [x] 4.2 Test HTML cleaning for descriptions (entities, tags, spacing)
- [x] 4.3 Test submissionProcedure parsing (handle missing, malformed JSON)
- [x] 4.4 Test URL construction (verify formats are correct)
- [x] 4.5 Test with missing/empty fields (no crashes, sensible fallbacks)

## 5. Integration Tests

- [x] 5.1 Run full `CallsFetcher.main()` with new field extraction
- [x] 5.2 Verify output `calls.json` contains all 12 new fields
- [x] 5.3 Validate JSON structure (no type mismatches, proper escaping)
- [x] 5.4 Test changelog generation includes new fields in change tracking

## 6. Code Quality

- [x] 6.1 Run flake8 on new/modified code (no style issues)
- [x] 6.2 Run pyright (no type errors)
- [x] 6.3 Update `RELEVANT_FIELDS` in `changelog.py` to include new metadata fields
- [x] 6.4 Add docstrings to new functions/helpers

## 7. Documentation

- [x] 7.1 Update README with description of enriched call fields
- [x] 7.2 Add comment in `_transform_record()` explaining Phase 2 scraping gate
- [x] 7.3 Update CHANGELOG.md (new section for enhanced metadata)
- [x] 7.4 Add CLI help text mentioning enriched metadata availability

## 8. Verification and Testing

- [x] 8.1 Run full test suite: `pytest --cov` (no regressions, coverage maintained)
- [x] 8.2 Manual verification: run `fetch-calls --force`, inspect calls.json for new fields
- [x] 8.3 Verify HTML cleaning works (no leftover tags, proper entity decoding)
- [x] 8.4 Check JSON file size increase (expected +20-30%)
- [x] 8.5 Verify workflow integration: changelog captures field changes
