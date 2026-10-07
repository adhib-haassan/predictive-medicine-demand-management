$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$venvPath = Join-Path $projectRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts/python.exe'
$dataDirectory = Join-Path $projectRoot 'data/zenodo'
$workbookPath = Join-Path $dataDirectory 'Consumos 2023-2024.xlsx'

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

& $venvPython -m pip install --upgrade pandas matplotlib jupyter scikit-learn statsmodels plotly mlxtend kaleido charset-normalizer==2.1.1 torch torchvision torchaudio openpyxl
if ($LASTEXITCODE -ne 0) { throw 'Failed to install Python packages.' }

if (-not (Test-Path $workbookPath)) {
	New-Item -ItemType Directory -Path $dataDirectory -Force | Out-Null
	Invoke-WebRequest -UseBasicParsing -Uri 'https://zenodo.org/api/records/18851842/files/Consumos%202023-2024.xlsx/content' -OutFile $workbookPath
}
$workbookHash = (Get-FileHash $workbookPath -Algorithm MD5).Hash.ToLowerInvariant()
if ($workbookHash -ne '1351cd4820ab2642f886b13e5a6ad074') {
	throw 'The Zenodo workbook checksum does not match the published record.'
}
