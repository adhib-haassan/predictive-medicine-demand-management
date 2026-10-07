#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo Activating environment
conda activate flower

echo Forecasting monthly medication consumption from Zenodo data
python ./flower/zenodo_forecast.py
