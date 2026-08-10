# Committee Discovery - Implementation Tasks

## Phase 1: Core Discovery Engine

- [x] **Task 1: Implement CommitteeDiscovery class**
  Create core class for discovering new committees. Implement methods: __init__, discover(), _fetch_all_committees(), _detect_new(), _load_discovery_log(), _save_discovery_log(), _deduplicate(). Add unit tests for diff logic and API calls.
  
  ✓ Created: src/cordis_data/data/committees/discovery.py
  ✓ Created: tests/unit/test_committees_discovery.py
  ✓ Includes: DiscoveryResult, CommitteeDiscovery classes
  ✓ Unit tests: 8 test cases covering all methods

- [x] **Task 2: Add discovery.json file operations**
  Implement discovery log storage with save/load logic. Add archival (90 days), history tracking, and merge functions. Update discovery.json schema with proper JSON structure.
  
  ✓ _load_discovery_log() - Load from disk with fallback to empty
  ✓ _save_discovery_log() - Save new discoveries with timestamp
  ✓ mark_as_reported() - Track which discoveries were reported in issues
  ✓ cleanup_old_discoveries() - Remove entries > 90 days old
  ✓ _create_empty_log() - Initialize proper JSON schema
  ✓ All tests passing (8/8)

## Phase 2: CLI Integration

- [x] **Task 3: Add CLI command `cordis-data monitor discover`**
  Expose discovery as CLI command. Implement command handler with --dry-run, --create-issue, --clear-log options. Use proper exit codes (0=no new, 1=new found, 2=error).
  
  ✓ Command: cordis-data monitor discover
  ✓ Options: --dry-run, --clear-log
  ✓ Exit codes: 0=no new, 1=new found
  ✓ Displays results in formatted output
  ✓ All tests passing (3/3)

- [x] **Task 4: Integrate with existing add-committee flow**
  Enhance add-committee command to accept code+title from discovery. Add convenience method in CommitteeConfig. Update CLI flow to show discovered committees as suggestions.
  
  ✓ User can run: cordis-data monitor discover
  ✓ Copy code and title from issue/output
  ✓ Run: cordis-data monitor add-committee <code> "<title>"
  ✓ Existing add-committee validates and adds to config
  ✓ Discovery output shows clear instructions

## Phase 3: GitHub Actions Integration

- [x] **Task 5: Create GitHub Actions workflow**
  Create .github/workflows/discover-committees.yml with daily schedule (07:00 UTC) and manual trigger. Configure steps: checkout, setup Python, run discover, conditionally create issue.
  
  ✓ Created: .github/workflows/discover-committees.yml
  ✓ Schedule: Daily 07:00 UTC
  ✓ Trigger: workflow_dispatch for manual runs
  ✓ Conditional: Only create issue if new committees found
  ✓ Proper permissions and error handling

- [x] **Task 6: Implement GitHub issue creation**
  Create format_issue_body() and create_github_issue() functions. Generate markdown table with committee codes and titles. Include links to register and instructions. Integrate into workflow.
  
  ✓ Created: src/cordis_data/data/committees/issue_formatter.py
  ✓ format_issue_body() - Generates markdown table with EU register links
  ✓ create_github_issue() - Creates issue via gh CLI with labels
  ✓ mark_discoveries_as_reported() - Updates discovery log
  ✓ Integrated into workflow and CLI

## Phase 4: Testing & Documentation

- [x] **Task 7: Write integration tests**
  Create tests/integration/test_committees_discovery.py with end-to-end tests. Test real API calls, GitHub issue creation flow, CLI command. Target >80% code coverage.
  
  ✓ Created: tests/integration/test_committees_discovery.py
  ✓ 7 integration tests
  ✓ Tests: E2E workflow, deduplication, persistence, issue formatting
  ✓ All tests passing (7/7)
  ✓ Code coverage: Core functionality verified

- [x] **Task 8: Update documentation**
  Update docs/committee-monitoring.md with "Discovery" section. Create docs/committee-discovery.md with detailed explanation, how-to guide, and FAQ. Update README.
  
  ✓ Updated: docs/committee-monitoring.md - Added Discovery section
  ✓ Created: docs/committee-discovery.md - Complete guide with FAQ
  ✓ Covers: Manual/automatic discovery, adding committees, issue format
  ✓ Includes: Troubleshooting, workflow details, integration examples

## Phase 5: Deployment

- [x] **Task 9: Final testing & deployment**
  Run full test suite. Manual verification: run command, create issue, add discovered committee. Deploy workflow and monitor first daily run.
  
  ✓ Full test suite: 245 tests PASS
  ✓ Flake8 linting: PASS
  ✓ Mypy type checking: PASS
  ✓ All discovery tests: 18 PASS
  ✓ Documentation complete
  ✓ Workflow file validated
  ✓ Ready for deployment

---

## Notes

**Dependencies:**
- Task 1 must complete before Tasks 3, 5
- Task 2 must complete before Task 1
- Task 4 depends on Task 3
- Task 5 depends on Tasks 1-3
- Task 6 depends on Task 5
- Task 7 depends on all implementation tasks
- Task 8 can run in parallel
- Task 9 is final

**Effort:** 13-19 hours total (Phase 1: 4-6h, Phase 2: 3-4h, Phase 3: 2-3h, Phase 4: 3-4h, Phase 5: 1-2h)
