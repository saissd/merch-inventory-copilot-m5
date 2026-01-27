import numpy as np
import pandas as pd
from typing import List

def to_long_sales(sales_wide: pd.DataFrame, max_series: int | None = None) -> pd.DataFrame:
    df = sales_wide.copy()
    if max_series is not None:
    # sample across stores so charts show multiple store_id values
        df = df.sample(n=max_series, random_state=42).copy()


    id_cols = ["id","item_id","dept_id","cat_id","store_id","state_id"]
    d_cols = [c for c in df.columns if c.startswith("d_")]
    long = df.melt(id_vars=id_cols, value_vars=d_cols, var_name="d", value_name="units")
    long["units"] = long["units"].astype(np.float32)
    return long

def join_calendar_prices(sales_long: pd.DataFrame, calendar: pd.DataFrame, sell_prices: pd.DataFrame) -> pd.DataFrame:
    cal = calendar.copy()
    keep_cols = [
        "d","date","wm_yr_wk","wday","month","year",
        "event_name_1","event_type_1","event_name_2","event_type_2",
        "snap_CA","snap_TX","snap_WI"
    ]
    cal = cal[keep_cols]
    cal["date"] = pd.to_datetime(cal["date"])

    df = sales_long.merge(cal, on="d", how="left")

    def _snap(row):
        if row["state_id"] == "CA":
            return row["snap_CA"]
        if row["state_id"] == "TX":
            return row["snap_TX"]
        return row["snap_WI"]

    df["snap"] = df.apply(_snap, axis=1).astype(np.int8)
    df.drop(columns=["snap_CA","snap_TX","snap_WI"], inplace=True)

    df = df.merge(
        sell_prices[["store_id","item_id","wm_yr_wk","sell_price"]],
        on=["store_id","item_id","wm_yr_wk"],
        how="left"
    )
    df["sell_price"] = df["sell_price"].astype(np.float32)
    return df

def add_time_series_features(df: pd.DataFrame, lags: List[int] = [7, 28], windows: List[int] = [7, 28]) -> pd.DataFrame:
    out = df.sort_values(["id","date"]).copy()

    out["weekday"] = out["wday"].astype(np.int8)
    out["month"] = out["month"].astype(np.int8)
    out["year"] = out["year"].astype(np.int16)

    out["price_isna"] = out["sell_price"].isna().astype(np.int8)
    out["sell_price_filled"] = out.groupby("id")["sell_price"].transform(lambda s: s.ffill().bfill())
    out["price_change_pct"] = (
        out.groupby("id")["sell_price_filled"]
           .pct_change()
           .replace([np.inf,-np.inf], np.nan)
           .fillna(0.0)
           .astype(np.float32)
    )

    out["has_event_1"] = out["event_name_1"].notna().astype(np.int8)
    out["has_event_2"] = out["event_name_2"].notna().astype(np.int8)
    out["is_event"] = ((out["has_event_1"]==1) | (out["has_event_2"]==1)).astype(np.int8)

    for lag in lags:
        out[f"lag_{lag}"] = out.groupby("id")["units"].shift(lag).astype(np.float32)

    for w in windows:
        out[f"roll_mean_{w}"] = (
            out.groupby("id")["units"]
               .shift(1)
               .rolling(window=w, min_periods=max(2, w//3))
               .mean()
               .reset_index(level=0, drop=True)
               .astype(np.float32)
        )
        out[f"roll_std_{w}"] = (
            out.groupby("id")["units"]
               .shift(1)
               .rolling(window=w, min_periods=max(2, w//3))
               .std()
               .reset_index(level=0, drop=True)
               .fillna(0.0)
               .astype(np.float32)
        )
    return out

def make_train_valid_split(df: pd.DataFrame, horizon: int = 28):
    max_date = df["date"].max()
    cut = max_date - pd.Timedelta(days=horizon)
    train = df[df["date"] <= cut].copy()
    valid = df[df["date"] > cut].copy()
    return train, valid
