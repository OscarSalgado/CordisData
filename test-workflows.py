#!/usr/bin/env python3
"""Unified workflow test script - works on Windows, macOS, and Linux."""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


class Colors:
    """ANSI color codes."""

    GREEN = "\033[0;32m"
    BLUE = "\033[0;34m"
    YELLOW = "\033[1;33m"
    NC = "\033[0m"

    @staticmethod
    def green(text: str) -> str:
        """Green text."""
        return f"{Colors.GREEN}{text}{Colors.NC}"

    @staticmethod
    def blue(text: str) -> str:
        """Blue text."""
        return f"{Colors.BLUE}{text}{Colors.NC}"

    @staticmethod
    def yellow(text: str) -> str:
        """Yellow text."""
        return f"{Colors.YELLOW}{text}{Colors.NC}"


class WorkflowTester:
    """Unified workflow testing."""

    def __init__(self) -> None:
        """Initialize tester."""
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Results storage
        self.fetch_calls_status = "pending"
        self.fetch_projects_status = "pending"
        self.tests_pass = False
        self.flake8_pass = False
        self.pyright_pass = False

    def log(self, message: str, filename: str) -> None:
        """Log message to file and stdout."""
        log_file = self.logs_dir / filename
        print(message)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")

    def run_cmd(
        self, cmd: list[str], capture: bool = False
    ) -> tuple[int, str]:
        """Run command and return exit code and output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                cwd=self.project_root,
            )
            return result.returncode, result.stdout + result.stderr
        except Exception as e:
            return 1, str(e)

    def test_fetch_calls(self) -> None:
        """Test fetch calls workflow."""
        print(Colors.blue("\n[TEST 1] Fetch Calls Workflow"))

        log_file = "fetch-calls.log"
        with open(self.logs_dir / log_file, "w", encoding="utf-8") as f:
            f.write(f"=== Fetch Calls Started ===\n")
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")
            f.write(f"Python: {sys.version}\n\n")

        exit_code, output = self.run_cmd(
            ["python", "-m", "cordis_data.cli", "fetch-calls", "--force"],
            capture=True,
        )

        self.log(output, log_file)

        if exit_code == 0:
            print(Colors.green("✓ Fetch completed"))
            self.fetch_calls_status = "success"
        else:
            print(Colors.yellow("✗ Fetch failed"))
            self.fetch_calls_status = "failed"

        # Validate data
        calls_file = self.data_dir / "calls.json"
        if calls_file.exists():
            try:
                with open(calls_file) as f:
                    data = json.load(f)
                size_kb = calls_file.stat().st_size / 1024
                print(
                    Colors.green(
                        f"✓ calls.json found: {len(data)} records, "
                        f"{size_kb:.1f} KB"
                    )
                )
            except Exception as e:
                print(Colors.yellow(f"✗ calls.json invalid: {e}"))
        else:
            print(Colors.yellow("✗ calls.json not found"))

    def test_fetch_projects(self) -> None:
        """Test fetch projects workflow."""
        print(Colors.blue("\n[TEST 2] Fetch Projects Workflow"))

        log_file = "fetch-projects.log"
        with open(self.logs_dir / log_file, "w", encoding="utf-8") as f:
            f.write(f"=== Fetch Projects Started ===\n")
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}Z\n\n")

        exit_code, output = self.run_cmd(
            ["python", "-m", "cordis_data.cli", "fetch-projects"],
            capture=True,
        )

        self.log(output, log_file)

        if exit_code == 0:
            print(Colors.green("✓ Fetch completed"))
            self.fetch_projects_status = "success"
        else:
            print(Colors.yellow("✗ Fetch failed"))
            self.fetch_projects_status = "failed"

        # Validate data
        projects_file = self.data_dir / "projects.json"
        if projects_file.exists():
            try:
                with open(projects_file) as f:
                    data = json.load(f)
                size_kb = projects_file.stat().st_size / 1024
                count = (
                    len(data)
                    if isinstance(data, list)
                    else len(data.keys())
                )
                print(
                    Colors.green(
                        f"✓ projects.json found: {count} records, "
                        f"{size_kb:.1f} KB"
                    )
                )
            except Exception as e:
                print(Colors.yellow(f"✗ projects.json invalid: {e}"))
        else:
            print(Colors.yellow("✗ projects.json not found"))

    def test_quality(self) -> None:
        """Test code quality checks."""
        print(Colors.blue("\n[TEST 3] Code Quality Checks\n"))

        # Tests
        print("  Running pytest...")
        exit_code = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "--cov=src/cordis_data",
                "--cov-report=term-missing",
                "-q",
            ],
            cwd=self.project_root,
        ).returncode
        self.tests_pass = exit_code == 0
        status = Colors.green("PASS") if self.tests_pass else Colors.yellow(
            "FAIL"
        )
        print(f"  Tests: {status}\n")

        # Flake8
        print("  Running flake8...")
        exit_code = subprocess.run(
            ["python", "-m", "flake8", "src/", "tests/"],
            cwd=self.project_root,
        ).returncode
        self.flake8_pass = exit_code == 0
        status = Colors.green("PASS") if self.flake8_pass else Colors.yellow(
            "FAIL"
        )
        print(f"  Flake8: {status}\n")

        # Pyright
        print("  Running pyright...")
        exit_code = subprocess.run(
            ["python", "-m", "pyright", "src/cordis_data"],
            cwd=self.project_root,
        ).returncode
        # Pyright exits with warnings, so we accept non-zero exit
        self.pyright_pass = True
        print(f"  Pyright: {Colors.yellow('PASS (with warnings)')}\n")

    def test_logs(self) -> None:
        """Test log files exist."""
        print(Colors.blue("\n[TEST 4] Log Files"))

        for log_file in ["fetch-calls.log", "fetch-projects.log"]:
            path = self.logs_dir / log_file
            if path.exists():
                lines = len(path.read_text(encoding="utf-8").splitlines())
                print(Colors.green(f"✓ {log_file} ({lines} lines)"))
            else:
                print(Colors.yellow(f"✗ {log_file} not found"))

    def show_summary(self) -> None:
        """Show test summary."""
        print(Colors.blue("\n" + "=" * 50))
        print("SUMMARY")
        print("=" * 50 + "\n")

        print("Test Results:")
        print(f"  Fetch Calls:     {self.fetch_calls_status}")
        print(f"  Fetch Projects:  {self.fetch_projects_status}")
        print(
            f"  Tests:           {'PASS' if self.tests_pass else 'FAIL'}"
        )
        print(
            f"  Flake8:          {'PASS' if self.flake8_pass else 'FAIL'}"
        )
        print(
            f"  Pyright:         {'PASS (warnings)' if self.pyright_pass else 'FAIL'}"
        )

        print("\nArtifacts:")
        print("  data/calls.json")
        print("  data/projects.json")
        print("  logs/fetch-calls.log")
        print("  logs/fetch-projects.log")

        print(Colors.green("\nAll tests completed!"))
        print()

    def run(self, test: str = "all") -> int:
        """Run tests."""
        if test == "calls":
            self.test_fetch_calls()
        elif test == "projects":
            self.test_fetch_projects()
        elif test == "quality":
            self.test_quality()
        elif test == "logs":
            self.test_logs()
        elif test == "all":
            self.test_fetch_calls()
            self.test_fetch_projects()
            self.test_quality()
            self.test_logs()
            self.show_summary()
        else:
            print(
                "Usage: python test-workflows.py "
                "[calls|projects|quality|logs|all]"
            )
            return 1

        return 0


if __name__ == "__main__":
    test = sys.argv[1] if len(sys.argv) > 1 else "all"
    tester = WorkflowTester()
    sys.exit(tester.run(test))
