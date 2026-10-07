#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo Creating environment
conda create --name flower python=3.8

echo Activating environment
conda activate flower

echo Fetching necessary packages
python -m pip install -U --pre 'flwr[simulation]'
conda install pandas matplotlib jupyter
pip install -U scikit-learn statsmodels plotly mlxtend kaleido charset-normalizer==2.1.1
pip3 install torch torchvision torchaudio openpyxl

DATA_DIR="$PROJECT_ROOT/data/zenodo"
WORKBOOK="$DATA_DIR/Consumos 2023-2024.xlsx"
mkdir -p "$DATA_DIR"
if [ ! -f "$WORKBOOK" ]; then
	curl -fL 'https://zenodo.org/api/records/18851842/files/Consumos%202023-2024.xlsx/content' -o "$WORKBOOK"
fi
ACTUAL_MD5="$(md5sum "$WORKBOOK" | cut -d ' ' -f 1)"
if [ "$ACTUAL_MD5" != "1351cd4820ab2642f886b13e5a6ad074" ]; then
	echo "The Zenodo workbook checksum does not match the published record." >&2
	exit 1
fi
