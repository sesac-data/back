param(
    [ValidateSet("limited", "full", "demo", "acceptance")]
    [string]$Mode = "limited"
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

function Assert-LastExitCode {
    param(
        [string]$Message
    )

    if ($LASTEXITCODE -ne 0) {
        throw $Message
    }
}

Write-Host "[verify] Mode: $Mode"
Write-Host "[verify] Checking required harness files"

$requiredFiles = @(
    "AGENTS.md",
    "docs/ARCHITECTURE.md",
    "docs/POLICY_SCHEMA.md",
    "docs/RULE_ENGINE.md",
    "docs/RECOMMENDATION_RULES.md",
    "docs/TEST_SCENARIOS.md",
    "docs/DEVELOPMENT_SETUP.md",
    "tasks/feature_list.json",
    "tasks/progress.md",
    "scripts/verify.sh",
    "scripts/verify.ps1",
    "scripts/run_recommendation_acceptance.py",
    "scripts/run_recommendation_smoke.py",
    "scripts/write_verification_report.py",
    ".env.example",
    "requirements-dev.txt"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "[verify] Missing required file: $file"
    }
}

Write-Host "[verify] Validating task JSON"
python -m json.tool tasks/feature_list.json | Out-Null
Assert-LastExitCode "[verify] tasks/feature_list.json is not valid JSON"

Write-Host "[verify] Checking existing tests are present"
$testFiles = Get-ChildItem -Path "match_agent_v0.8/match_agent_v0.8" -Filter "test_*.py" -File | Sort-Object Name
if ($testFiles.Count -lt 1) {
    throw "[verify] No existing Python tests found"
}
Write-Host "[verify] Found $($testFiles.Count) Python test files"

$dbDependentTests = @(
    "test_db_connection.py",
    "test_policy_load.py",
    "test_recommendation_history_service.py"
)

$testRoot = Join-Path $RootDir "match_agent_v0.8/match_agent_v0.8"

if ($Mode -eq "full") {
    Write-Host "[verify] Running full Python test set"
    python -c "import pytest" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "[verify] Full mode requires pytest. Install with: python -m pip install -r requirements-dev.txt"
    }

    Push-Location $testRoot
    try {
        python -m pytest
        Assert-LastExitCode "[verify] Full Python test set failed"
    } finally {
        Pop-Location
    }
} elseif ($Mode -in @("limited", "acceptance")) {
    Write-Host "[verify] Running limited Python test set"
    foreach ($testFile in $testFiles) {
        if ($dbDependentTests -contains $testFile.Name) {
            Write-Host "[verify] Skipping $($testFile.Name): DB-dependent test; limited mode does not require SQLAlchemy/PostgreSQL"
            continue
        }

        Write-Host "[verify] Running $($testFile.Name)"
        Push-Location $testRoot
        try {
            python $testFile.Name
            Assert-LastExitCode "[verify] Python test failed: $($testFile.Name)"
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "[verify] Skipping limited Python test set: demo mode runs frontend build plus acceptance/E2E only"
}

$frontendDir = Join-Path $RootDir "match_agent_v0.8/match_agent_v0.8/frontend"
$nodeModules = Join-Path $frontendDir "node_modules"
if (Test-Path -LiteralPath $nodeModules -PathType Container) {
    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npmCmd) {
        Write-Host "[verify] Running frontend build"
        Push-Location $frontendDir
        try {
            npm.cmd run build
            Assert-LastExitCode "[verify] Frontend build failed"
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "[verify] Skipping frontend build: npm.cmd is not available"
    }
} else {
    Write-Host "[verify] Skipping frontend build: frontend node_modules not found"
}

if ($Mode -in @("demo", "acceptance")) {
    Write-Host "[verify] Running backend acceptance"
    python scripts\run_recommendation_acceptance.py
    Assert-LastExitCode "[verify] Backend acceptance failed"

    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        throw "[verify] Frontend E2E requires npm.cmd"
    }

    if (-not (Test-Path -LiteralPath $nodeModules -PathType Container)) {
        throw "[verify] Frontend E2E requires frontend node_modules. Run npm.cmd install in the frontend directory."
    }

    Write-Host "[verify] Running frontend E2E"
    Push-Location $frontendDir
    try {
        npm.cmd run test:e2e
        Assert-LastExitCode "[verify] Frontend E2E failed"
    } finally {
        Pop-Location
    }

    Write-Host "[verify] Writing Markdown verification report"
    $commandText = "powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode $Mode"
    $limitedArgs = @()
    if ($Mode -eq "acceptance") {
        $limitedArgs += "--limited-ran"
    }
    python scripts\write_verification_report.py --command $commandText --mode $Mode @limitedArgs
    Assert-LastExitCode "[verify] Markdown verification report failed"
}

Write-Host "[verify] OK"
