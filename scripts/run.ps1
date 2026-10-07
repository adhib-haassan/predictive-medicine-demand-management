$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$venvPython = Join-Path $projectRoot '.venv/Scripts/python.exe'

if (-not (Test-Path $venvPython)) {
	throw 'Virtual environment not found. Run scripts/install.ps1 first.'
}

Write-Host 'Forecasting monthly medication consumption from Zenodo data'
& $venvPython (Join-Path $projectRoot 'flower/zenodo_forecast.py')
if ($LASTEXITCODE -ne 0) { throw 'Zenodo medication forecast failed.' }
