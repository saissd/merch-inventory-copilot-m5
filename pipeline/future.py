import pandas as pd
import numpy as np

from .forecast import FEATURE_COLS

CAT_COLS = ["item_id", "dept_id", "cat_id", "store_id", "state_id"]

def _cast_cats(X: pd.DataFrame) -> pd.DataFrame:
    for c in CAT_COLS:
        if c in X.columns:
            X[c] = X[c].astype("category")
    return X

def build_future_frame(history_feat: pd.DataFrame, calendar: pd.DataFrame, sell_prices: pd.DataFrame, horizon: int = 28) -> pd.DataFrame:
    hist = history_feat.sort_values(["id", "date"]).copy()
    last_date = hist["date"].max()

    cal = calendar.copy()
    cal["date"] = pd.to_datetime(cal["date"])
    future_cal = cal[cal["date"] > last_date].sort_values("date").head(horizon).copy()

    base_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
    ids = hist[base_cols].drop_duplicates()

    future = ids.merge(future_cal, how="cross")

    def _snap(row):
        if row["state_id"] == "CA":
            return row["snap_CA"]
        if row["state_id"] == "TX":
            return row["snap_TX"]
        return row["snap_WI"]

    future["snap"] = future.apply(_snap, axis=1).astype(np.int8)

    future = future.merge(
        sell_prices[["store_id", "item_id", "wm_yr_wk", "sell_price"]],
        on=["store_id", "item_id", "wm_yr_wk"],
        how="left",
    )
    future["sell_price"] = future["sell_price"].astype(np.float32)
    future["sell_price_filled"] = future.groupby("id")["sell_price"].transform(lambda s: s.ffill().bfill())
    future["price_isna"] = future["sell_price"].isna().astype(np.int8)
    future["price_change_pct"] = (
        future.groupby("id")["sell_price_filled"]
        .pct_change()
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .astype(np.float32)
    )

    future["weekday"] = future["wday"].astype(np.int8)
    future["month"] = future["month"].astype(np.int8)
    future["year"] = future["year"].astype(np.int16)
    future["has_event_1"] = future["event_name_1"].notna().astype(np.int8)
    future["has_event_2"] = future["event_name_2"].notna().astype(np.int8)
    future["is_event"] = ((future["has_event_1"] == 1) | (future["has_event_2"] == 1)).astype(np.int8)

    return future

def recursive_forecast(model, history_feat: pd.DataFrame, future_base: pd.DataFrame) -> pd.DataFrame:
    hist = history_feat.sort_values(["id", "date"]).copy()
    fut = future_base.sort_values(["id", "date"]).copy()

    out_rows = []
    for _id, h in hist.groupby("id", sort=False):
        f = fut[fut["id"] == _id].sort_values("date").copy()
        if f.empty:
            continue

        units_list = h.sort_values("date")["units"].astype(np.float32).tolist()

        for i in range(len(f)):
            def safe_lag(k):
                return units_list[-k] if len(units_list) >= k else np.nan

            lag_7 = safe_lag(7)
            lag_28 = safe_lag(28)

            def roll_stats(w):
                window = units_list[-w:] if len(units_list) >= w else units_list
                if len(window) == 0:
                    return (np.nan, 0.0)
                return (float(np.mean(window)), float(np.std(window)))

            rm7, rs7 = roll_stats(7)
            rm28, rs28 = roll_stats(28)

            row = f.iloc[i].copy()
            row["lag_7"] = np.float32(lag_7) if np.isfinite(lag_7) else np.nan
            row["lag_28"] = np.float32(lag_28) if np.isfinite(lag_28) else np.nan
            row["roll_mean_7"] = np.float32(rm7) if np.isfinite(rm7) else np.nan
            row["roll_std_7"] = np.float32(rs7)
            row["roll_mean_28"] = np.float32(rm28) if np.isfinite(rm28) else np.nan
            row["roll_std_28"] = np.float32(rs28)

            X = pd.DataFrame([row])[FEATURE_COLS].copy()
            X = _cast_cats(X)

            yhat = float(model.predict(X)[0])
            yhat = max(yhat, 0.0)

            out = row.copy()
            out["pred_units"] = np.float32(yhat)
            out_rows.append(out)

            units_list.append(np.float32(yhat))

    return pd.DataFrame(out_rows)
