import pandas as pd
import numpy as np
from typing import Tuple, Dict
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_squared_error
from joblib import dump

from .utils import wape

FEATURE_COLS = [
    "item_id","dept_id","cat_id","store_id","state_id",
    "weekday","month","year","snap","is_event",
    "sell_price_filled","price_change_pct","price_isna",
    "lag_7","lag_28","roll_mean_7","roll_std_7","roll_mean_28","roll_std_28",
]

def _prep_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    X = df[FEATURE_COLS].copy()
    for c in ["item_id","dept_id","cat_id","store_id","state_id"]:
        X[c] = X[c].astype("category")
    y = df["units"].values.astype(np.float32)
    return X, y

def train_forecast_model(train_df: pd.DataFrame, valid_df: pd.DataFrame):
    X_train, y_train = _prep_xy(train_df.dropna(subset=["lag_28","lag_7"]))
    X_valid, y_valid = _prep_xy(valid_df.dropna(subset=["lag_28","lag_7"]))

    model = LGBMRegressor(
        n_estimators=1200,
        learning_rate=0.05,
        num_leaves=64,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    pred = model.predict(X_valid).astype(np.float32)
    pred = np.clip(pred, 0.0, None)

    metrics = {
        "valid_rmse": float(mean_squared_error(y_valid, pred, squared=False)),
        "valid_wape": float(wape(y_valid, pred)),
        "valid_sum_y": float(np.sum(y_valid)),
    }

    out = valid_df.dropna(subset=["lag_28","lag_7"]).copy()
    out["pred_units"] = pred
    return model, metrics, out

def save_model(model, path: str) -> None:
    dump(model, path)
