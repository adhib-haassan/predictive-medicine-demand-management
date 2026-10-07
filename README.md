# fl-blood-supply-chain

Federated learning for blood supply chain. Simulation code repo for the paper [Federated Blood Supply Chain Demand Forecasting: A Case Study](https://openreview.net/forum?id=2c0hdQDvf5g), published in KDD 2023 International Workshop on Federated Learning for Distributed Data Mining.



## Overview

Federated learning offers a decentralized approach when it comes to training a machine learning model. It allows multiple parties to collabortively train a predictive model without sharing their data. This project aims to explore the possibility of using federated learning to train a predictive model for blood supply chain.

<p align="center">
  <img src="docs/images/fl-bscm.png" width="600" /><br />
  Figure 1. Project architecture overview.
</p>

This repo contains the code for the project. We are exploring the possibility of using federated learning to train a predictive model for blood supply chain using simulated data based on ARIMA model.

In this project, we are using Flower, a federated learning framework for PyTorch, to simulate the federated learning process. We are using a LSTM model as the baseline for the centralized training. The data pipeline is shown in the figure below.

<p align="center">
  <img src="docs/images/lstm.png" width="600" /><br />
  Figure 2. Proposed data pipeline.
</p>


## Installation
- Run the installation script for your shell from the repository root. It installs dependencies and downloads all 16 files from the Zenodo record into `data/zenodo/`, verifying each published checksum.
```bash
bash scripts/install.sh
```

On Windows, PowerShell creates a local `.venv` and installs dependencies there:
```powershell
.\scripts\install.ps1
```

## Usage
The default runner forecasts monthly medication consumption from the Zenodo workbook:
```bash
bash scripts/run.sh
```

In PowerShell:
```powershell
.\scripts\run.ps1
```

The Zenodo download includes consumption, inventory, stock parameters, stock levels, formulary, XYZ classifications, purchase arrivals and lead times, waste, stockout claims, overstock costs, procurement/finance costs, plus the record's example code and documentation. The default forecast currently uses `Consumos 2023-2024.xlsx`; the other operational files are available locally for further analysis but are not inputs to this forecaster.

The consumption workbook contains 370 medication records from one public oncology hospital, with monthly values for 2023-2024. The default pipeline trains a pooled monthly forecaster across medication histories; products are not treated as separate hospitals, and this is not a federated evaluation. The chronological holdout is July-December 2024 and uses one-step-ahead rolling forecasts with observed prior months. Forecast rows are saved to `flower/evaluation/zenodo_forecasts.csv`, and the model checkpoint is saved to `flower/savedmodels/zenodo_model.pt`.

The previous ARIMA/federated simulation remains available through `bash scripts/run_arima_fl.sh` or `.\scripts\run_arima_fl.ps1`. Generate its synthetic client data with `python arima/generate_case_balanced_iid.py`.

## Results

The Zenodo source workbook is released under CC BY 4.0 and contains operational data without patient-level or identifiable information.

## Data Attribution

Fernando, R. (2026). *Dataset and Code for Risk-Informed Data Analytics for Sustainable Pharmaceutical Supply: A Governance Framework for Public Oncology Hospitals* [Dataset]. Zenodo. [https://doi.org/10.5281/zenodo.18851842](https://doi.org/10.5281/zenodo.18851842). CC BY 4.0.

## Reference

\[15\] Maryam Motamedi, Na Li, Douglas G Down, and Nancy M Heddle. 2021. Demand
forecasting for platelet usage: from univariate time series to multivariate models.
[arXiv preprint arXiv:2101.02305](https://arxiv.org/abs/2101.02305) (2021)

## Citation

```
@inproceedings{wei2023federated,
  title={Federated Blood Supply Chain Demand Forecasting: A Case Study},
  author={Wei, Hanzhe and Li, Na and Wu, Jiajun and Zhou, Jiayu and Drew, Steve},
  booktitle={International Workshop on Federated Learning for Distributed Data Mining},
  year={2023}
}
```
