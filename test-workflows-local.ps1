param([string]$Test = "all")

$ErrorActionPreference = "Continue"
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_ROOT

function Write-Success { Write-Host -ForegroundColor Green "$args" }
function Write-Info { Write-Host -ForegroundColor Blue "$args" }
function Write-Warn { Write-Host -ForegroundColor Yellow "$args" }

function Test-FetchCalls {
  Write-Info "[TEST 1] Fetch Calls Workflow"
  New-Item -ItemType Directory -Path logs, src\data -Force | Out-Null

  "=== Starting calls fetch ===" | Tee-Object -FilePath logs/fetch-calls.log -Append
  "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')" | Tee-Object -FilePath logs/fetch-calls.log -Append
  "Python: $(python --version 2>&1)" | Tee-Object -FilePath logs/fetch-calls.log -Append

  try {
    & cordis-data fetch-calls --force 2>&1 | Tee-Object -FilePath logs/fetch-calls.log -Append
    Write-Success "Fetch completed"
    $script:FETCH_CALLS = "success"
  }
  catch {
    Write-Warn "Fetch failed: $_"
    $script:FETCH_CALLS = "failed"
  }

  if (Test-Path src\data\calls.json) {
    $size = (Get-Item src\data\calls.json).Length / 1024
    Write-Success "Found calls.json ($([math]::Round($size)) KB)"
  }
  else {
    Write-Warn "calls.json not found"
  }
}

function Test-FetchProjects {
  Write-Info "[TEST 2] Fetch Projects Workflow"
  New-Item -ItemType Directory -Path logs, src\data -Force | Out-Null

  "=== Starting projects fetch ===" | Tee-Object -FilePath logs/fetch-projects.log -Append
  "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')" | Tee-Object -FilePath logs/fetch-projects.log -Append

  try {
    & cordis-data fetch-projects 2>&1 | Tee-Object -FilePath logs/fetch-projects.log -Append
    Write-Success "Fetch completed"
    $script:FETCH_PROJECTS = "success"
  }
  catch {
    Write-Warn "Fetch failed: $_"
    $script:FETCH_PROJECTS = "failed"
  }

  if (Test-Path src\data\projects.json) {
    $size = (Get-Item src\data\projects.json).Length / 1024
    Write-Success "Found projects.json ($([math]::Round($size)) KB)"
  }
  else {
    Write-Warn "projects.json not found"
  }
}

function Test-Quality {
  Write-Info "[TEST 3] Code Quality"

  Write-Host "Running tests..."
  & pytest --cov=src/cordis_data --cov-report=term-missing -q 2>&1
  $script:TESTS_PASS = ($LASTEXITCODE -eq 0)

  if ($script:TESTS_PASS) {
    Write-Success "Tests: PASS"
  } else {
    Write-Warn "Tests: FAIL"
  }

  Write-Host "Running flake8..."
  & flake8 src/cordis_data tests --config=.flake8 2>&1 | Select-Object -First 5
  $script:FLAKE8_PASS = ($LASTEXITCODE -eq 0)

  if ($script:FLAKE8_PASS) {
    Write-Success "Flake8: PASS"
  } else {
    Write-Warn "Flake8: FAIL"
  }

  Write-Host "Running pyright..."
  & pyright src/cordis_data tests --outputjson 2>&1 | Out-Null
  $script:PYRIGHT_PASS = ($LASTEXITCODE -eq 0)

  if ($script:PYRIGHT_PASS) {
    Write-Success "Pyright: PASS"
  } else {
    Write-Warn "Pyright: FAIL"
  }
}

function Test-Logs {
  Write-Info "[TEST 4] Log Files"

  if (Test-Path logs/fetch-calls.log) {
    $lines = @(Get-Content logs/fetch-calls.log).Count
    Write-Success "fetch-calls.log ($lines lines)"
  }

  if (Test-Path logs/fetch-projects.log) {
    $lines = @(Get-Content logs/fetch-projects.log).Count
    Write-Success "fetch-projects.log ($lines lines)"
  }
}

function Show-Summary {
  Write-Info "`n=========================="
  Write-Info "SUMMARY"
  Write-Info "==========================`n"

  Write-Host "Status:"
  Write-Host "  Fetch Calls:   $($script:FETCH_CALLS)"
  Write-Host "  Fetch Projects: $($script:FETCH_PROJECTS)"
  Write-Host "  Tests:         $(if ($script:TESTS_PASS) { 'PASS' } else { 'FAIL' })"
  Write-Host "  Flake8:        $(if ($script:FLAKE8_PASS) { 'PASS' } else { 'FAIL' })"
  Write-Host "  Pyright:       $(if ($script:PYRIGHT_PASS) { 'PASS' } else { 'FAIL' })"

  Write-Host "`nArtifacts:"
  Write-Host "  data/calls.json"
  Write-Host "  data/projects.json"
  Write-Host "  logs/fetch-calls.log"
  Write-Host "  logs/fetch-projects.log"

  Write-Success "`nAll tests completed!"
}

switch ($Test) {
  "calls" { Test-FetchCalls }
  "projects" { Test-FetchProjects }
  "quality" { Test-Quality }
  "logs" { Test-Logs }
  "all" {
    Test-FetchCalls
    Test-FetchProjects
    Test-Quality
    Test-Logs
    Show-Summary
  }
  default {
    Write-Host "Usage: .\test-workflows-local.ps1 [calls|projects|quality|logs|all]"
  }
}
