# ClinIQ - Windows Setup Checker

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ClinIQ - Windows Environment Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Core Tools:" -ForegroundColor Yellow

# Python
$r = python --version 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] Python: $r" -ForegroundColor Green }
else { Write-Host "  [MISSING] Python - not found" -ForegroundColor Red }

# pip
$r = pip --version 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] pip: $r" -ForegroundColor Green }
else { Write-Host "  [MISSING] pip - not found" -ForegroundColor Red }

# Java
$r = java -version 2>&1 | Select-Object -First 1
if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] Java: $r" -ForegroundColor Green }
else { Write-Host "  [MISSING] Java - not found" -ForegroundColor Red }

# Git
$r = git --version 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] Git: $r" -ForegroundColor Green }
else { Write-Host "  [MISSING] Git - not found" -ForegroundColor Red }

# Node
$r = node --version 2>&1
if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] Node.js: $r" -ForegroundColor Green }
else { Write-Host "  [MISSING] Node.js - not found" -ForegroundColor Red }

Write-Host ""
Write-Host "Editors:" -ForegroundColor Yellow

# VS Code
$r = code --version 2>&1 | Select-Object -First 1
if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] VS Code: $r" -ForegroundColor Green }
else { Write-Host "  [MISSING] VS Code - not found" -ForegroundColor Red }

Write-Host ""
Write-Host "Python Packages:" -ForegroundColor Yellow

$packages = @("duckdb", "langchain", "langgraph", "chromadb", "fastapi", "streamlit", "faker", "pandas")
foreach ($pkg in $packages) {
    $r = python -c "import $pkg; print($pkg.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] $pkg : $r" -ForegroundColor Green }
    else { Write-Host "  [MISSING] $pkg" -ForegroundColor Red }
}

Write-Host ""
Write-Host "Project Files:" -ForegroundColor Yellow

$projectPath = "D:\Project\AI-Healthcare\cliniq"
if (Test-Path $projectPath) {
    Write-Host "  [OK] cliniq folder exists" -ForegroundColor Green
} else {
    Write-Host "  [MISSING] cliniq folder not found" -ForegroundColor Red
}

$dbPath = "D:\Project\AI-Healthcare\cliniq\data\omop.duckdb"
if (Test-Path $dbPath) {
    $size = [math]::Round((Get-Item $dbPath).Length / 1KB)
    Write-Host "  [OK] omop.duckdb found (${size}KB)" -ForegroundColor Green
} else {
    Write-Host "  [MISSING] omop.duckdb not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
