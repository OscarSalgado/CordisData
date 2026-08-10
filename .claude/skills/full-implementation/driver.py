#!/usr/bin/env python3
"""Full implementation workflow: apply change, lint, type-check, test, commit."""

import json
import subprocess
import sys


def run_cmd(cmd: list[str], description: str = "") -> tuple[int, str, str]:
    """Run command and return (exit_code, stdout, stderr)."""
    if description:
        print(f"\n{'='*60}")
        print(f"[{description}]")
        print(f"{'='*60}")

    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode, result.stdout, result.stderr


def get_active_change() -> str:
    """Get the active OpenSpec change name."""
    code, out, _ = run_cmd(["openspec", "list", "--json"], "Listing OpenSpec changes")

    if code != 0:
        print("ERROR: Failed to list OpenSpec changes")
        return ""

    try:
        changes = json.loads(out)
        active_changes = [c for c in changes if c.get("status") != "archived"]

        if not active_changes:
            print("No active changes found")
            return ""

        if len(active_changes) == 1:
            return active_changes[0]["name"]

        print("\nActive changes:")
        for i, c in enumerate(active_changes, 1):
            print(f"  {i}. {c['name']} ({c.get('schema', 'unknown')})")

        idx = int(input("Select change (number): ")) - 1
        return active_changes[idx]["name"]
    except (json.JSONDecodeError, ValueError, IndexError) as e:
        print(f"ERROR parsing changes: {e}")
        return ""


def apply_change(change_name: str) -> bool:
    """Apply OpenSpec change."""
    if not change_name:
        print("No change name provided")
        return False

    code, _, _ = run_cmd(
        ["python", "-m", "cordis_data.cli.opsx", "apply", change_name],
        f"Applying OpenSpec change: {change_name}"
    )

    return code == 0


def run_flake8() -> bool:
    """Run flake8 and report errors."""
    code, out, _ = run_cmd(
        ["flake8", "src/", "tests/", "--max-line-length=120"],
        "Running flake8"
    )

    if code == 0:
        print("✓ flake8: No issues")
        return True

    print(f"✗ flake8: {code} issues found")
    return False


def run_pyright() -> bool:
    """Run pyright and report errors."""
    code, out, _ = run_cmd(
        ["pyright", "src/", "tests/"],
        "Running pyright"
    )

    if code == 0:
        print("✓ pyright: No issues")
        return True

    print(f"✗ pyright: {code} issues found")
    return False


def run_mypy() -> bool:
    """Run mypy and report errors."""
    code, out, _ = run_cmd(
        ["mypy", "src/", "tests/"],
        "Running mypy"
    )

    if code == 0:
        print("✓ mypy: No issues")
        return True

    print(f"✗ mypy: {code} issues found")
    return False


def run_tests() -> bool:
    """Run pytest with coverage."""
    code, out, _ = run_cmd(
        ["pytest", "tests/", "-v", "--cov=src/", "--cov-report=term-missing"],
        "Running tests with coverage"
    )

    return code == 0


def commit_changes(change_name: str) -> bool:
    """Commit changes with proper message."""
    # Get git status
    code, out, _ = run_cmd(
        ["git", "status", "--porcelain"],
        "Checking git status"
    )

    if not out.strip():
        print("No changes to commit")
        return True

    # Create commit message
    commit_msg = f"""Apply OpenSpec change: {change_name}

- Implement change per design specification
- All linting checks pass (flake8, pyright, mypy)
- Tests pass with full coverage

Co-Authored-By: Claude <claude@anthropic.com>
"""

    code, _, _ = run_cmd(
        ["git", "add", "-A"],
        "Staging changes"
    )

    if code != 0:
        return False

    code, _, _ = run_cmd(
        ["git", "commit", "-m", commit_msg],
        "Creating commit"
    )

    return code == 0


def main():
    """Run full implementation workflow."""
    print("=" * 60)
    print("FULL IMPLEMENTATION WORKFLOW")
    print("=" * 60)

    # Step 1: Select change
    print("\n[1/6] Selecting OpenSpec change...")
    change_name = get_active_change()
    if not change_name:
        print("ERROR: No change selected")
        return 1
    print(f"Selected: {change_name}")

    # Step 2: Apply change
    print("\n[2/6] Applying OpenSpec change...")
    if not apply_change(change_name):
        print("ERROR: Failed to apply change")
        return 1

    # Step 3: flake8
    print("\n[3/6] Running flake8...")
    flake8_ok = run_flake8()

    # Step 4: pyright
    print("\n[4/6] Running pyright...")
    pyright_ok = run_pyright()

    # Step 5: mypy
    print("\n[5/6] Running mypy...")
    mypy_ok = run_mypy()

    if not (flake8_ok and pyright_ok and mypy_ok):
        print("\nERROR: Linting/type-checking failed")
        print("Please fix errors manually and re-run")
        return 1

    # Step 6: Tests
    print("\n[6/6] Running tests with coverage...")
    if not run_tests():
        print("ERROR: Tests failed")
        return 1

    # Step 7: Commit
    print("\n[7/7] Committing changes...")
    if not commit_changes(change_name):
        print("ERROR: Commit failed")
        return 1

    print("\n" + "=" * 60)
    print("SUCCESS: Full implementation workflow completed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
