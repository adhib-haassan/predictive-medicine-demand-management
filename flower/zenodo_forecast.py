from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_squared_error
from torch.utils.data import DataLoader, TensorDataset

from ml_models import get_model
from myconstants import DEVICE, DROPOUT, EPOCH, HIDDEN_DIM, LAYER_DIM, LEARNING_RATE, MODEL, WEIGHT_DECAY


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = PROJECT_ROOT / "data" / "zenodo" / "Consumos 2023-2024.xlsx"
MONTH_COUNT = 24
MONTH_START = pd.Timestamp("2023-01-01")
HISTORY_LENGTH = 7
TRAIN_MONTH_COUNT = 18
FEATURE_COUNT = 11
BATCH_SIZE = 64


def _load_monthly_consumption(workbook_path):
    raw = pd.read_excel(workbook_path, sheet_name=0, header=3)
    if raw.shape[1] < 30:
        raise ValueError("The consumption workbook does not contain 24 monthly columns.")

    required_columns = {"Código", "Medicamento", "UM"}
    if not required_columns.issubset(raw.columns):
        raise ValueError("The consumption workbook is missing expected medication columns.")

    monthly = raw.iloc[:, 6:30].apply(pd.to_numeric, errors="coerce")
    valid_rows = (
        raw["Código"].notna()
        & raw["Medicamento"].notna()
        & pd.to_numeric(raw["Código"], errors="coerce").notna()
    )
    products = raw.loc[valid_rows].reset_index(drop=True)
    monthly = monthly.loc[valid_rows].reset_index(drop=True)

    if monthly.shape[1] != MONTH_COUNT or monthly.isna().any().any():
        raise ValueError("The workbook must contain complete monthly consumption for 2023-2024.")
    if (monthly < 0).any().any():
        raise ValueError("Monthly consumption values cannot be negative.")

    codes = pd.to_numeric(products["Código"], errors="raise").astype("int64")
    if codes.duplicated().any():
        raise ValueError("Medication codes must be unique to keep each time series separate.")

    return products, monthly, codes


def _features(history, target_month):
    month_angle = 2 * np.pi * (target_month.month - 1) / 12
    calendar = np.array(
        [
            target_month.month / 12,
            np.sin(month_angle),
            np.cos(month_angle),
            target_month.year - 2023,
        ],
        dtype=np.float32,
    )
    return np.concatenate((history.astype(np.float32), calendar))


def _build_examples(products, monthly, codes):
    months = pd.date_range(MONTH_START, periods=MONTH_COUNT, freq="MS")
    train_features = []
    train_targets = []
    test_features = []
    test_targets = []
    test_rows = []
    scale_by_code = {}

    for row_index, code in enumerate(codes):
        values = monthly.iloc[row_index].to_numpy(dtype=np.float64)
        if not np.any(values):
            continue

        logged_values = np.log1p(values)
        scale = float(logged_values[:TRAIN_MONTH_COUNT].max())
        if scale <= 0:
            continue

        normalized = (logged_values / scale).astype(np.float32)
        scale_by_code[str(code)] = scale
        for target_index in range(HISTORY_LENGTH, MONTH_COUNT):
            features = _features(
                normalized[target_index - HISTORY_LENGTH:target_index],
                months[target_index],
            )
            target = normalized[target_index]

            if target_index < TRAIN_MONTH_COUNT:
                train_features.append(features)
                train_targets.append(target)
                continue

            test_features.append(features)
            test_targets.append(target)
            test_rows.append(
                {
                    "date": months[target_index],
                    "code": str(code),
                    "medicine": str(products.iloc[row_index]["Medicamento"]),
                    "unit": str(products.iloc[row_index]["UM"]),
                    "actual_consumption": float(values[target_index]),
                    "scale": scale,
                }
            )

    if not train_features or not test_features:
        raise ValueError("The workbook does not provide enough active medication histories to train and test.")

    return (
        np.asarray(train_features, dtype=np.float32),
        np.asarray(train_targets, dtype=np.float32).reshape(-1, 1),
        np.asarray(test_features, dtype=np.float32),
        np.asarray(test_targets, dtype=np.float32).reshape(-1, 1),
        pd.DataFrame(test_rows),
        scale_by_code,
    )


def main():
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(
            f"Zenodo workbook not found at {WORKBOOK_PATH}. Run scripts/install.ps1 first."
        )

    torch.manual_seed(42)
    np.random.seed(42)

    products, monthly, codes = _load_monthly_consumption(WORKBOOK_PATH)
    x_train, y_train, x_test, y_test, test_rows, scale_by_code = _build_examples(
        products, monthly, codes
    )
    print(
        f"Loaded {len(scale_by_code)} medication histories; "
        f"training windows: {len(x_train)}, holdout windows: {len(x_test)}."
    )
    print("Chronological holdout: July-December 2024.")

    train_data = TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train))
    train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
    model_params = {
        "input_dim": FEATURE_COUNT,
        "hidden_dim": HIDDEN_DIM,
        "layer_dim": LAYER_DIM,
        "output_dim": 1,
        "dropout_prob": DROPOUT,
    }
    model = get_model(MODEL, model_params).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    loss_fn = torch.nn.MSELoss()

    for epoch in range(EPOCH):
        model.train()
        epoch_losses = []
        for features, targets in train_loader:
            features = features.unsqueeze(1).to(DEVICE)
            targets = targets.to(DEVICE)
            optimizer.zero_grad()
            loss = loss_fn(model(features), targets)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch + 1}/{EPOCH}, loss: {np.mean(epoch_losses):.5f}")

    model.eval()
    with torch.no_grad():
        predictions = model(torch.from_numpy(x_test).unsqueeze(1).to(DEVICE)).cpu().numpy().ravel()

    predictions = np.maximum(predictions, 0)
    test_rows["forecast_consumption"] = np.expm1(predictions * test_rows["scale"].to_numpy())
    test_rows = test_rows.drop(columns="scale")
    scaled_log_rmse = np.sqrt(mean_squared_error(y_test.ravel(), predictions))

    output_dir = PROJECT_ROOT / "flower" / "evaluation"
    model_dir = PROJECT_ROOT / "flower" / "savedmodels"
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    test_rows.to_csv(output_dir / "zenodo_forecasts.csv", index=False)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "feature_count": FEATURE_COUNT,
            "history_length": HISTORY_LENGTH,
            "scale_by_code": scale_by_code,
            "train_month_count": TRAIN_MONTH_COUNT,
        },
        model_dir / "zenodo_model.pt",
    )

    print(f"Scaled-log holdout RMSE: {scaled_log_rmse:.5f}")
    print(f"Forecasts saved to {output_dir / 'zenodo_forecasts.csv'}")


if __name__ == "__main__":
    main()