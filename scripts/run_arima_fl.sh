#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo Activating environment
conda activate flower

echo Starting ARIMA-based Centralized Training
python ./flower/central.py

echo Starting Federated Learning Simulation
python ./flower/fl_simulation.py

echo Plotting Evaluation Metrics
python ./flower/saved_model_eval.py