import numpy as np
import pandas as pd
from typing import Tuple

def estimate_elasticity_loglog(df: pd.DataFrame) -> pd.DataFrame:
    gcols = ["item_id","store_id"]
    rows = []
    for (item, store), g in df.dropna(subset=["sell_price_filled"]).groupby(gcols):
        if len(g) < 30:
            continue
        x = np.log(g["sell_price_filled"].values.astype(np.float32) + 1e-6)
        y = np.log(g["units"].values.astype(np.float32) + 1.0)

        x_mean = x.mean()
        y_mean = y.mean()
        denom = np.sum((x - x_mean) ** 2)
        if denom <= 1e-9:
            continue
        b = float(np.sum((x - x_mean) * (y - y_mean)) / denom)
        rows.append({"item_id": item, "store_id": store, "elasticity": b, "n_obs": int(len(g))})

    # IMPORTANT: always return these columns
    out = pd.DataFrame(rows, columns=["item_id","store_id","elasticity","n_obs"])
    return out

def optimize_markdown(
    df: pd.DataFrame,
    elasticity_df: pd.DataFrame,
    cost_fraction: float = 0.60,
    markdown_grid: Tuple[float, ...] = (0.0, 0.10, 0.20, 0.30, 0.40),
    horizon_days: int = 28,
    inventory_days_of_supply: int = 21,
) -> pd.DataFrame:
    max_date = df["date"].max()
    window = df[df["date"] > (max_date - pd.Timedelta(days=horizon_days))].copy()

    base = (
        window.groupby(["item_id","store_id"], as_index=False)
              .agg(base_demand_per_day=("pred_units","mean"),
                   base_price=("sell_price_filled","last"),
                   avg_units=("units","mean"))
    )
    if elasticity_df is None or elasticity_df.empty:
        elasticity_df = pd.DataFrame(columns=["item_id","store_id","elasticity"])

    base = base.merge(elasticity_df[["item_id","store_id","elasticity"]], on=["item_id","store_id"], how="left")
    base["elasticity"] = base["elasticity"].fillna(-1.2)

    recs = []
    for _, r in base.iterrows():
        P0 = float(r["base_price"]) if pd.notna(r["base_price"]) else np.nan
        if not np.isfinite(P0) or P0 <= 0:
            continue
        e = float(r["elasticity"])
        D0 = float(r["base_demand_per_day"]) if np.isfinite(r["base_demand_per_day"]) else 0.0
        if D0 <= 0:
            continue

        inventory_on_hand = D0 * inventory_days_of_supply
        cost = P0 * cost_fraction

        best = None
        for md in markdown_grid:
            P = P0 * (1.0 - md)
            if P <= cost:
                continue
            D = D0 * (P / P0) ** e
            expected_units = min(D * horizon_days, inventory_on_hand)
            profit = (P - cost) * expected_units

            if (best is None) or (profit > best["profit"]):
                best = {
                    "item_id": r["item_id"],
                    "store_id": r["store_id"],
                    "base_price": P0,
                    "markdown": md,
                    "opt_price": P,
                    "elasticity": e,
                    "base_demand_per_day": D0,
                    "opt_demand_per_day": D,
                    "inventory_on_hand": inventory_on_hand,
                    "profit": profit,
                }

        if best is not None:
            recs.append(best)

    out = pd.DataFrame(recs).sort_values("profit", ascending=False).reset_index(drop=True)
    return out
