## 1. H2020 API Client Setup

- [x] 1.1 Extend CordisClient to support H2020 API queries
- [x] 1.2 Implement H2020 project lookup method (by projectId)
- [x] 1.3 Implement H2020 bulk search method (get all projects, paginated)
- [x] 1.4 Add rate limiting for H2020 API calls (reuse existing TokenBucket)
- [x] 1.5 Add error handling and retry logic for H2020 calls

## 2. H2020Enricher Class Structure

- [x] 2.1 Create `src/cordis_data/data/h2020.py` with H2020Enricher class
- [x] 2.2 Implement `__init__` with CordisClient dependency injection
- [x] 2.3 Implement `_load_h2020_index()` method to pre-load all projects
- [x] 2.4 Implement index data structure (dict keyed by projectId, acronym, team members)
- [x] 2.5 Add error handling for index load failures (graceful degradation)

## 3. Matching Strategies

- [x] 3.1 Implement `_match_by_projectid()` strategy (confidence 0.99)
- [x] 3.2 Implement `_match_by_acronym()` strategy (case-insensitive exact, confidence 0.95)
- [x] 3.3 Implement `_match_by_team_overlap()` strategy (3+ orgs, confidence 0.75-0.85)
- [x] 3.4 Implement `_match_by_title_similarity()` strategy (Levenshtein + team, confidence 0.70-0.80)
- [x] 3.5 Implement `_match_by_keywords()` strategy (2+ overlaps, confidence 0.60-0.75)
- [x] 3.6 Implement matching orchestrator: try strategies in order, return best (greedy)

## 4. Metadata Extraction & Transformation

- [x] 4.1 Extract organisations from H2020 project (name, country, role)
- [x] 4.2 Extract publications from H2020 project (title, DOI, URL)
- [x] 4.3 Extract datasets from H2020 project (title, DOI, URL)
- [x] 4.4 Extract keywords/subjects from H2020 project
- [x] 4.5 Build `h2020_related` dict structure with all metadata fields

## 5. Integration with ProjectsFetcher

- [x] 5.1 Modify ProjectsFetcher to instantiate H2020Enricher
- [x] 5.2 Add H2020 enrichment call in ProjectsFetcher.main() after CORDIS enrichment
- [x] 5.3 Update project records with h2020_related field (only if match found)
- [x] 5.4 Ensure graceful failure: H2020 errors don't block project writing

## 6. Unit Tests for H2020Enricher

- [x] 6.1 Test projectId exact match (verify confidence 0.99)
- [x] 6.2 Test acronym exact match (verify case-insensitive, confidence 0.95)
- [x] 6.3 Test team overlap detection (3+, 5+, edge cases)
- [x] 6.4 Test title similarity (Levenshtein distance calculation)
- [x] 6.5 Test keywords overlap matching
- [x] 6.6 Test matching orchestration (greedy strategy, early exit)
- [x] 6.7 Test index loading and error handling
- [x] 6.8 Test metadata extraction (organisations, publications, datasets)
- [x] 6.9 Test with no match found (h2020_related absent from output)

## 7. Integration Tests

- [x] 7.1 Test full enrichment workflow with ProjectsFetcher
- [x] 7.2 Test projects with H2020 matches get h2020_related field
- [x] 7.3 Test projects without matches have no h2020_related field
- [x] 7.4 Test projects.json output is valid JSON with all fields
- [x] 7.5 Test enrichment continues if H2020 index fails to load

## 8. Code Quality

- [x] 8.1 Run flake8 on h2020.py (no style issues)
- [x] 8.2 Add type hints for all methods and fields
- [x] 8.3 Run pyright to verify type coverage
- [x] 8.4 Add docstrings to H2020Enricher class and all methods
- [x] 8.5 Update RELEVANT_FIELDS in changelog.py to include h2020_related

## 9. Documentation & Configuration

- [x] 9.1 Document H2020 enrichment in README
- [x] 9.2 Add comment in ProjectsFetcher.main() explaining H2020 stage
- [x] 9.3 Add CLI help text mentioning H2020 enrichment availability
- [x] 9.4 Update CHANGELOG.md with new capability
- [x] 9.5 Document match confidence threshold recommendation (0.80+)

## 10. Verification & Testing

- [x] 10.1 Run full test suite: `pytest --cov` (no regressions)
- [x] 10.2 Manual verification: run `fetch-projects --force`, inspect projects.json for h2020_related
- [x] 10.3 Verify high-confidence matches (0.90+) are present and correct
- [x] 10.4 Check JSON file size increase (expected +10-15% per enriched project)
- [x] 10.5 Verify H2020 index loads in < 5 seconds
- [x] 10.6 Test graceful failure: disable H2020 API and verify enrichment continues
