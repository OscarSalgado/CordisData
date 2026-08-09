## 1. Core CLI Module Setup

- [x] 1.1 Create `src/cordis_data/cli/explorer.py` module
- [x] 1.2 Create data loader: load calls.json and projects.json into memory
- [x] 1.3 Build in-memory indices (by cluster, acronym, keywords, H2020 lineage)
- [x] 1.4 Create filter builder (AND logic for multiple criteria)

## 2. Search Commands

- [x] 2.1 Implement `search-calls` command with Click decorators
- [x] 2.2 Add filters: --cluster, --keyword, --status, --budget-min, --deadline-after
- [x] 2.3 Implement `search-projects` command
- [x] 2.4 Add H2020 lineage lookup for projects (show ancestors)

## 3. View Commands

- [x] 3.1 Implement `view-call` command (show full metadata)
- [x] 3.2 Show H2020 related calls (from enrichment)
- [x] 3.3 Show projects that won the call
- [x] 3.4 Implement `view-project` command
- [x] 3.5 Show H2020 ancestors with confidence scores

## 4. Output Formatting

- [x] 4.1 Create table formatter (using tabulate library)
- [x] 4.2 Implement JSON output format
- [x] 4.3 Add --format flag to all commands (default: table)
- [x] 4.4 Implement pagination for large result sets (default: 50 per page)

## 5. Export Commands

- [x] 5.1 Implement `export` command for batch export
- [x] 5.2 Export filtered calls to JSON
- [x] 5.3 Export filtered calls to CSV
- [x] 5.4 Export projects with H2020 lineage to CSV

## 6. CLI Integration

- [x] 6.1 Register new commands in existing `cordis_data.cli` entry point
- [x] 6.2 Add help text and docstrings to all commands
- [x] 6.3 Update main `cordis-data --help` to show explorer commands

## 7. Unit Tests

- [x] 7.1 Test search-calls filtering (cluster, keywords, status, budget)
- [x] 7.2 Test search-projects with H2020 lineage
- [x] 7.3 Test view-call command output
- [x] 7.4 Test view-project with H2020 ancestors
- [x] 7.5 Test table formatting
- [x] 7.6 Test JSON output format
- [x] 7.7 Test CSV export
- [x] 7.8 Test edge cases (empty results, missing data, malformed JSON)

## 8. Integration Tests

- [x] 8.1 Test full workflow: search-calls → view-call → show winners
- [x] 8.2 Test full workflow: search-projects → show H2020 lineage
- [x] 8.3 Test export workflow with filtered data
- [x] 8.4 Verify output consistency (table vs JSON should have same data)

## 9. Code Quality

- [x] 9.1 Run flake8 on explorer.py (no style issues)
- [x] 9.2 Add type hints to all functions
- [x] 9.3 Run pyright for type coverage
- [x] 9.4 Add docstrings to all public functions

## 10. Documentation

- [x] 10.1 Add README section: "Data Explorer"
- [x] 10.2 Document all commands with examples
- [x] 10.3 Provide usage examples for researchers
- [x] 10.4 Document filter combinations and syntax

## 11. Verification

- [x] 11.1 Run full test suite (no regressions)
- [x] 11.2 Manual test: search calls by cluster
- [x] 11.3 Manual test: view call with H2020 lineage
- [x] 11.4 Manual test: export filtered projects to CSV
- [x] 11.5 Verify table formatting is readable
