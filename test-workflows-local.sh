#!/bin/bash
# Local workflow test script - simulates GitHub Actions environments

set -e

echo "=================================================="
echo "  CordisData Workflow Tests (Local)"
echo "=================================================="

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Fetch Calls
test_fetch_calls() {
  echo -e "\n${BLUE}[TEST 1] Fetch Calls Workflow${NC}"

  mkdir -p logs data

  echo "=== Starting calls fetch ===" | tee -a logs/fetch-calls.log
  echo "Timestamp: $(date -u +'%Y-%m-%d %H:%M:%S UTC')" | tee -a logs/fetch-calls.log
  echo "Python version: $(python --version)" | tee -a logs/fetch-calls.log
  echo "Installed packages:" | tee -a logs/fetch-calls.log
  pip list | tee -a logs/fetch-calls.log
  echo "" | tee -a logs/fetch-calls.log

  if cordis-data fetch-calls --force 2>&1 | tee -a logs/fetch-calls.log; then
    echo "Fetch completed successfully" | tee -a logs/fetch-calls.log
    FETCH_STATUS="success"
  else
    echo "Fetch failed" | tee -a logs/fetch-calls.log
    FETCH_STATUS="failed"
  fi

  echo "=== Data Validation ===" | tee -a logs/fetch-calls.log

  HAS_DATA="false"
  if [ -f data/calls.json ]; then
    size=$(wc -c < data/calls.json)
    count=$(python -c "import json; print(len(json.load(open('data/calls.json'))))" 2>/dev/null || echo "unknown")
    echo "calls.json exists" | tee -a logs/fetch-calls.log
    echo "  Size: $((size / 1024)) KB" | tee -a logs/fetch-calls.log
    echo "  Records: $count" | tee -a logs/fetch-calls.log
    HAS_DATA="true"
  else
    echo "calls.json not found" | tee -a logs/fetch-calls.log
  fi

  if [ -f data/.metadata.json ]; then
    echo "metadata.json exists" | tee -a logs/fetch-calls.log
    cat data/.metadata.json | tee -a logs/fetch-calls.log
  else
    echo "metadata.json not found" | tee -a logs/fetch-calls.log
  fi

  echo ""
  echo -e "${GREEN}✓ Fetch Calls Test Complete${NC}"
  echo "  Status: $FETCH_STATUS"
  echo "  Data: $HAS_DATA"
  echo "  Logs: logs/fetch-calls.log"
}

# Test 2: Fetch Projects
test_fetch_projects() {
  echo -e "\n${BLUE}[TEST 2] Fetch Projects Workflow${NC}"

  mkdir -p logs data

  echo "=== Starting projects fetch ===" | tee -a logs/fetch-projects.log
  echo "Timestamp: $(date -u +'%Y-%m-%d %H:%M:%S UTC')" | tee -a logs/fetch-projects.log
  echo "Python version: $(python --version)" | tee -a logs/fetch-projects.log
  echo "Installed packages:" | tee -a logs/fetch-projects.log
  pip list | tee -a logs/fetch-projects.log
  echo "" | tee -a logs/fetch-projects.log

  if cordis-data fetch-projects 2>&1 | tee -a logs/fetch-projects.log; then
    echo "Fetch completed successfully" | tee -a logs/fetch-projects.log
    FETCH_STATUS="success"
  else
    echo "Fetch failed" | tee -a logs/fetch-projects.log
    FETCH_STATUS="failed"
  fi

  echo "=== Data Validation ===" | tee -a logs/fetch-projects.log

  HAS_DATA="false"
  if [ -f data/projects.json ]; then
    size=$(wc -c < data/projects.json)
    count=$(python -c "import json; print(len(json.load(open('data/projects.json'))))" 2>/dev/null || echo "unknown")
    echo "projects.json exists" | tee -a logs/fetch-projects.log
    echo "  Size: $((size / 1024)) KB" | tee -a logs/fetch-projects.log
    echo "  Records: $count" | tee -a logs/fetch-projects.log
    HAS_DATA="true"
  else
    echo "projects.json not found" | tee -a logs/fetch-projects.log
  fi

  if [ -f data/.metadata.json ]; then
    echo "metadata.json exists" | tee -a logs/fetch-projects.log
    cat data/.metadata.json | tee -a logs/fetch-projects.log
  else
    echo "metadata.json not found" | tee -a logs/fetch-projects.log
  fi

  echo ""
  echo -e "${GREEN}✓ Fetch Projects Test Complete${NC}"
  echo "  Status: $FETCH_STATUS"
  echo "  Data: $HAS_DATA"
  echo "  Logs: logs/fetch-projects.log"
}

# Test 3: Run tests and linting
test_quality() {
  echo -e "\n${BLUE}[TEST 3] Code Quality Checks${NC}"

  echo "Running pytest..."
  if pytest --cov=src/cordis_data --cov-report=term-missing -v; then
    echo -e "${GREEN}✓ Tests passed${NC}"
    TESTS_PASS=true
  else
    echo -e "${YELLOW}✗ Tests failed${NC}"
    TESTS_PASS=false
  fi

  echo ""
  echo "Running flake8..."
  if flake8 src/cordis_data tests --config=.flake8; then
    echo -e "${GREEN}✓ Flake8 passed${NC}"
    FLAKE8_PASS=true
  else
    echo -e "${YELLOW}✗ Flake8 failed${NC}"
    FLAKE8_PASS=false
  fi

  echo ""
  echo "Running pyright..."
  if pyright src/cordis_data tests; then
    echo -e "${GREEN}✓ Pyright passed${NC}"
    PYRIGHT_PASS=true
  else
    echo -e "${YELLOW}✗ Pyright failed${NC}"
    PYRIGHT_PASS=false
  fi
}

# Test 4: Check logs
test_logs() {
  echo -e "\n${BLUE}[TEST 4] Log Files${NC}"

  if [ -f logs/fetch-calls.log ]; then
    echo -e "${GREEN}✓ fetch-calls.log${NC}"
    echo "  Size: $(wc -c < logs/fetch-calls.log) bytes"
    echo "  Lines: $(wc -l < logs/fetch-calls.log)"
  else
    echo -e "${YELLOW}✗ fetch-calls.log not found${NC}"
  fi

  if [ -f logs/fetch-projects.log ]; then
    echo -e "${GREEN}✓ fetch-projects.log${NC}"
    echo "  Size: $(wc -c < logs/fetch-projects.log) bytes"
    echo "  Lines: $(wc -l < logs/fetch-projects.log)"
  else
    echo -e "${YELLOW}✗ fetch-projects.log not found${NC}"
  fi
}

# Summary
show_summary() {
  echo -e "\n${BLUE}=================================================="
  echo "  SUMMARY"
  echo "==================================================${NC}"

  echo ""
  echo "Test Results:"
  echo "  Fetch Calls:     $FETCH_STATUS"
  echo "  Fetch Projects:  $FETCH_STATUS"
  echo "  Tests:           $([ "$TESTS_PASS" = true ] && echo 'PASS' || echo 'FAIL')"
  echo "  Flake8:          $([ "$FLAKE8_PASS" = true ] && echo 'PASS' || echo 'FAIL')"
  echo "  Pyright:         $([ "$PYRIGHT_PASS" = true ] && echo 'PASS' || echo 'FAIL')"

  echo ""
  echo "Artifacts:"
  echo "  data/calls.json"
  echo "  data/projects.json"
  echo "  logs/fetch-calls.log"
  echo "  logs/fetch-projects.log"

  echo ""
  echo -e "${GREEN}All tests completed!${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Review logs: tail logs/fetch-calls.log"
  echo "  2. Check data: python -m json.tool data/calls.json | head -20"
  echo "  3. Run full tests: pytest -v"
  echo "  4. Push to GitHub to test actual workflows"
}

# Main
case "${1:-all}" in
  calls)
    test_fetch_calls
    ;;
  projects)
    test_fetch_projects
    ;;
  quality)
    test_quality
    ;;
  logs)
    test_logs
    ;;
  all)
    test_fetch_calls
    test_fetch_projects
    test_quality
    test_logs
    show_summary
    ;;
  *)
    echo "Usage: $0 [calls|projects|quality|logs|all]"
    exit 1
    ;;
esac
