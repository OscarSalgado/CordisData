## ADDED Requirements

### Requirement: H2020 project matching and enrichment

The system SHALL automatically match Horizon projects to related H2020 projects using multi-strategy matching and enrich project records with H2020 metadata.

#### Scenario: Exact projectId match
- **WHEN** a Horizon project's ID matches a H2020 project ID in the index
- **THEN** the system matches with confidence 0.99 and returns H2020 metadata immediately (no further strategies attempted)

#### Scenario: Acronym exact match
- **WHEN** a Horizon project's acronym exactly matches (case-insensitive) a H2020 project acronym
- **THEN** the system matches with confidence 0.95 and returns H2020 metadata

#### Scenario: Team overlap match
- **WHEN** a Horizon project shares 3+ organisations with a H2020 project
- **THEN** the system matches with confidence proportional to overlap: 0.75 (3 orgs) to 0.85 (5+ orgs)

#### Scenario: Title similarity match
- **WHEN** a Horizon project's title has Levenshtein distance < 30% from H2020 project title AND teams overlap
- **THEN** the system matches with confidence 0.70–0.80 based on similarity score and team overlap

#### Scenario: Keyword/subject overlap match
- **WHEN** a Horizon project shares keywords or subjects with a H2020 project (2+ matches)
- **THEN** the system matches with confidence 0.60–0.75 based on overlap count

### Requirement: Match confidence scoring

The system SHALL include a confidence score (0.0–1.0) with each H2020 match to enable users to filter by reliability threshold.

#### Scenario: High-confidence match
- **WHEN** matching completes with confidence ≥ 0.90
- **THEN** the field `h2020_related.matchConfidence` is set to that score and the matched strategy name is recorded

#### Scenario: Low-confidence match
- **WHEN** only low-confidence strategies (keywords, title similarity < 0.70) produce a match
- **THEN** the system includes `matchConfidence` < 0.75 so users can filter by applying a higher threshold

#### Scenario: No match found
- **WHEN** no H2020 project meets any matching strategy
- **THEN** the `h2020_related` field is absent from the project record (not null or empty)

### Requirement: H2020 metadata enrichment fields

When a match is found, the system SHALL populate the `h2020_related` object with the following fields from the matched H2020 project:

#### Scenario: Organisation details included
- **WHEN** a match is found
- **THEN** the `h2020_related.organisations` array includes name, country, and role (coordinator/partner) for each organisation

#### Scenario: Publications and datasets included
- **WHEN** a match is found
- **THEN** the `h2020_related.publications` and `h2020_related.datasets` arrays are populated with titles, DOIs, and URLs

#### Scenario: Keywords and subject metadata included
- **WHEN** a match is found
- **THEN** the `h2020_related.keywords` array includes all keywords/subjects from the H2020 project

### Requirement: Pre-loaded H2020 index

The system SHALL load the complete H2020 project index at enrichment startup (not per-project).

#### Scenario: Index loads on startup
- **WHEN** H2020Enricher is initialized
- **THEN** all ~30K H2020 projects are loaded from CORDIS into an in-memory index

#### Scenario: Matching uses indexed data
- **WHEN** enriching a Horizon project
- **THEN** matching queries the in-memory index (no network calls during enrichment)

#### Scenario: Index failure handling
- **WHEN** H2020 index fails to load
- **THEN** enrichment continues without H2020 matches (graceful degradation)

### Requirement: Match strategy selection

The system SHALL use a greedy strategy: execute matching strategies in order of confidence and stop at first successful match.

#### Scenario: Early exit on high-confidence match
- **WHEN** a Horizon project matches via projectId (confidence 0.99)
- **THEN** the system returns immediately without attempting lower-confidence strategies

#### Scenario: Fallback to lower strategies
- **WHEN** no exact match is found but title similarity + team overlap produces confidence ≥ 0.70
- **THEN** the system accepts that match and returns (does not continue to keyword matching)

#### Scenario: All strategies exhausted
- **WHEN** all strategies are attempted and the best match has confidence < 0.60
- **THEN** the system rejects the match and omits `h2020_related` field from the record
