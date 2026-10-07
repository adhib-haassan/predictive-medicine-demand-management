$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$venvPath = Join-Path $projectRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts/python.exe'

if (-not (Test-Path $venvPython)) {
	Write-Host 'Creating virtual environment'
	python -m venv $venvPath
	if ($LASTEXITCODE -ne 0) { throw 'Failed to create the virtual environment.' }
}

Write-Host 'Installing required packages'
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Failed to upgrade pip.' }

& $venvPython -m pip install --upgrade --pre 'flwr[simulation]'
if ($LASTEXITCODE -ne 0) { throw 'Failed to install Flower.' }

& $venvPython -m pip install --upgrade pandas matplotlib jupyter scikit-learn statsmodels plotly mlxtend kaleido charset-normalizer==2.1.1 torch torchvision torchaudio
if ($LASTEXITCODE -ne 0) { throw 'Failed to install Python packages.' }
