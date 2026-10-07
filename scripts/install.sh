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
pip3 install torch torchvision torchaudio
