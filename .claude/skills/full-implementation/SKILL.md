---
name: full-implementation
description: Apply OpenSpec change, lint, type-check, test, and commit
---

# Full Implementation Workflow

Orchestrates the complete change implementation pipeline: apply OpenSpec change → fix linting → fix type errors → run tests → commit.

Runs these checks in sequence:
1. Apply OpenSpec change (interactive selection if multiple active)
2. Run flake8 (PEP 8 linting)
3. Run pyright (static type checking)
4. Run mypy (runtime type checking)
5. Run pytest with full coverage (must pass)
6. Git commit with proper message

## Prerequisites

- Python 3.12+
- Git
- OpenSpec configured
- Dependencies installed: `pip install flake8 pyright mypy pytest pytest-cov`

## Agent Path

Run the driver script:

```bash
python .claude/skills/full-implementation/driver.py
```

The script will:
1. List active OpenSpec changes (prompt to select if multiple)
2. Apply the selected change
3. Run each linting/type-checking tool in sequence
4. Run tests with coverage reporting
5. Commit all changes with proper message

## What It Does

```
Step 1: Select OpenSpec change
        (auto-select if only one active)

Step 2: Apply change
        → runs openspec-apply-change
        → marks all tasks complete
        
Step 3: flake8 check
        → PEP 8 validation
        → exit on failures
        
Step 4: pyright check
        → type annotation validation
        → exit on failures
        
Step 5: mypy check
        → static type validation
        → exit on failures
        
Step 6: pytest + coverage
        → run all tests
        → require passing tests
        → report coverage
        
Step 7: git commit
        → stage all changes
        → create commit with change name
        → include co-author metadata
```

## Output

The script prints:
- Each tool's output in real-time
- Summary: pass/fail for each step
- Coverage report (pytest output)
- Git commit hash on success

## Exit Codes

- `0` — All steps passed, changes committed
- `1` — Any step failed; see error output above

## Gotchas

- **Multiple active changes:** Script prompts for selection. Type the number (1-indexed).
- **Linting failures block progress:** Fix errors manually, then restart the script.
- **Test failures block commit:** Fix tests, re-run script.
- **No changes after apply:** Commit step skipped gracefully.
- **Missing OpenSpec change:** Script exits with error message.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "No active changes" | No OpenSpec change defined | Create change with `/opsx:new` |
| flake8 exits with errors | Code style issues | Fix manually, re-run script |
| pyright exits with errors | Type annotation errors | Fix type hints, re-run script |
| pytest fails | Test failures or coverage gap | Fix code/tests, re-run script |
| git commit fails | Uncommitted files conflict | Check `git status`, resolve conflicts |

## Files

- `.claude/skills/full-implementation/driver.py` — the driver script (300 lines)
- `.claude/skills/full-implementation/SKILL.md` — this file
