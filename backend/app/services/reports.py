import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from app.core.config import settings

def _read_json(path: str) -> Dict[str, Any]:
    import json
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path): return pd.DataFrame()
    return pd.read_csv(path)

def summary():
    s = _read_json(os.path.join(settings.REPORTS_DIR, "summary_metrics.json"))
    s["retrain_metrics"] = _read_json(os.path.join(settings.REPORTS_DIR, "retrain_metrics.json"))
    return s

def future_forecast(store_id: Optional[str]=None, item_id: Optional[str]=None, limit: int=1000):
    df = _read_csv(os.path.join(settings.REPORTS_DIR, "future_forecast_next_28d.csv"))
    if df.empty: return []
    if store_id: df = df[df["store_id"] == store_id]
    if item_id: df = df[df["item_id"] == item_id]
    df = df.sort_values("date").head(limit)
    return df.to_dict(orient="records")

def recs(kind: str, store_id: Optional[str]=None, limit: int=200):
    file_map = {
        "inventory": "recommendations_inventory.csv",
        "pricing": "recommendations_pricing.csv",
        "assortment": "recommendations_assortment.csv",
        "sql_top_items": "sql_top_items.csv",
    }
    path = file_map.get(kind)
    if not path: return []

    df = _read_csv(os.path.join(settings.REPORTS_DIR, path))
    if df.empty: return []

    if store_id and "store_id" in df.columns:
        df = df[df["store_id"] == store_id]

    # --- ✅ INVENTORY ACTION UPGRADE (actionable fields) ---
    if kind == "inventory":
        # If pipeline doesn't provide inventory_on_hand, we simulate a deterministic demo value:
        # assume ~7 days on hand based on avg_pred.
        if "inventory_on_hand" not in df.columns and "avg_pred" in df.columns:
            df["inventory_on_hand"] = (df["avg_pred"].astype(float).fillna(0.0) * 7.0).round(3)

        if "reorder_point" in df.columns and "inventory_on_hand" in df.columns:
            df["order_qty"] = (df["reorder_point"].astype(float) - df["inventory_on_hand"].astype(float)).clip(lower=0).round(3)

        if "avg_pred" in df.columns and "inventory_on_hand" in df.columns:
            denom = df["avg_pred"].astype(float).replace(0, np.nan)
            df["days_of_supply"] = (df["inventory_on_hand"].astype(float) / denom).replace([np.inf, -np.inf], np.nan).fillna(0.0).round(3)

        # Put important columns early (so UI shows them)
        preferred = ["item_id","store_id","avg_pred","inventory_on_hand","days_of_supply","reorder_point","safety_stock","order_qty"]
        cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
        df = df[cols]

    # Sort for presentability
    if "profit" in df.columns:
        df = df.sort_values("profit", ascending=False)
    elif "reorder_point" in df.columns:
        df = df.sort_values("reorder_point", ascending=False)

    return df.head(limit).to_dict(orient="records")
