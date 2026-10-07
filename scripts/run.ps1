$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$venvPython = Join-Path $projectRoot '.venv/Scripts/python.exe'

if (-not (Test-Path $venvPython)) {
	throw 'Virtual environment not found. Run scripts/install.ps1 first.'
}

Write-Host 'Starting Centralized Training'
& $venvPython (Join-Path $projectRoot 'flower/central.py')
if ($LASTEXITCODE -ne 0) { throw 'Centralized training failed.' }

Write-Host 'Starting Federated Learning Simulation'
& $venvPython (Join-Path $projectRoot 'flower/fl_simulation.py')
if ($LASTEXITCODE -ne 0) { throw 'Federated learning simulation failed.' }

Write-Host 'Plotting Evaluation Metrics'
& $venvPython (Join-Path $projectRoot 'flower/saved_model_eval.py')
if ($LASTEXITCODE -ne 0) { throw 'Evaluation plotting failed.' }
